import ast

ACOES = {'dock', 'undock', 'info', 'startToPose', 'getPoseStamped'}
DIRECOES = {'NORTH', 'NORTH_WEST', 'WEST', 'SOUTH_WEST', 'SOUTH', 'SOUTH_EAST', 'EAST', 'NORTH_EAST'}
VARIAVEIS = {'goal', 'dest'}
MAX_COORD = 50.0
MAX_COMANDOS = 10


class Recusado(Exception):
    pass


def limpar(texto):
    linhas = [l for l in texto.strip().splitlines() if not l.strip().startswith('```')]
    return '\n'.join(linhas).strip()


def _numero(no):
    if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)):
        return float(no.value)
    if (isinstance(no, ast.UnaryOp) and isinstance(no.op, (ast.USub, ast.UAdd))
            and isinstance(no.operand, ast.Constant) and isinstance(no.operand.value, (int, float))):
        v = float(no.operand.value)
        return -v if isinstance(no.op, ast.USub) else v
    return None


def _expr(no, destinos):
    n = _numero(no)
    if n is not None:
        return
    if isinstance(no, ast.Constant) and isinstance(no.value, str) and len(no.value) <= 100:
        return
    if isinstance(no, ast.List):
        for e in no.elts:
            _expr(e, destinos)
        return
    if isinstance(no, ast.Name) and no.id in VARIAVEIS:
        return
    if (isinstance(no, ast.Attribute) and isinstance(no.value, ast.Name)
            and no.value.id == 'TurtleBot4Directions' and no.attr in DIRECOES):
        return
    if isinstance(no, ast.Subscript) and isinstance(no.value, ast.Subscript):
        _expr(no.value, destinos)
        s = no.slice
        if isinstance(s, ast.Constant) and isinstance(s.value, int):
            return
        if (isinstance(s, ast.Slice) and all(
                p is None or (isinstance(p, ast.Constant) and isinstance(p.value, int))
                for p in (s.lower, s.upper, s.step))):
            return
        raise Recusado('indexação não permitida')
    if isinstance(no, ast.Subscript) and isinstance(no.value, ast.Name):
        if no.value.id == 'destinations':
            if (isinstance(no.slice, ast.Constant) and isinstance(no.slice.value, str)
                    and no.slice.value in destinos):
                return
            raise Recusado('destino desconhecido')
        if no.value.id == 'dest':
            s = no.slice
            if isinstance(s, ast.Constant) and isinstance(s.value, int):
                return
            if (isinstance(s, ast.Slice) and all(
                    p is None or (isinstance(p, ast.Constant) and isinstance(p.value, int))
                    for p in (s.lower, s.upper, s.step))):
                return
        raise Recusado('indexação não permitida')
    if isinstance(no, ast.Call):
        _chamada(no, destinos)
        return
    raise Recusado('expressão não permitida: ' + type(no).__name__)


def _chamada(no, destinos):
    f = no.func
    if not (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
            and f.value.id == 'navigator' and f.attr in ACOES):
        raise Recusado('chamada não permitida')
    if no.keywords:
        raise Recusado('argumentos nomeados não permitidos')
    for a in no.args:
        _expr(a, destinos)
    if f.attr == 'getPoseStamped' and no.args and isinstance(no.args[0], ast.List):
        for e in no.args[0].elts:
            v = _numero(e)
            if v is None or abs(v) > MAX_COORD:
                raise Recusado('coordenada fora do limite')


def validar(codigo, destinos):
    arvore = ast.parse(codigo)
    if not arvore.body:
        raise Recusado('vazio')
    if len(arvore.body) > MAX_COMANDOS:
        raise Recusado('longo demais')
    for no in arvore.body:
        if isinstance(no, ast.Expr) and isinstance(no.value, ast.Call):
            _chamada(no.value, destinos)
        elif (isinstance(no, ast.Assign) and len(no.targets) == 1
              and isinstance(no.targets[0], ast.Name) and no.targets[0].id in VARIAVEIS):
            _expr(no.value, destinos)
        else:
            raise Recusado('instrução não permitida: ' + type(no).__name__)
    return arvore
