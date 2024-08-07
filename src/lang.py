from typing import Optional, TextIO, BinaryIO, Type, Any, cast
from pathlib import Path

import os
import sys
import subprocess
import shutil
from dataclasses import dataclass
from itertools import batched


from .classes import (
	AbstractProgram,
	Engine,
	Token,
	FlowInfo,

	Type,
	Symbol,
	Procedure,
)

from .engine import Compiler, Interpreter 
from .typechecker import (
	TypeChecker,
	TypeCheckerException,
	NotEnoughTokens,
	InvalidType,
	Types,
)

from .lexer import (
	Tokenize,
	TokenInfo,
	TokenTypes,

	OpTypes,
	PreprocTypes,
	Intrinsics,
	Operands,
	FlowControl,

)

from .errors import (
	TypeWarning,
	LangExceptions,
	UnknownToken,
	InvalidSyntax,
	SymbolRedefined,
	FileError,
	Stopped,
	Reporting,
)

from .error_trace import (
	warn, trace,
)

def PUSH(val: int, info=None)    -> Token: return Token(OpTypes.OP_PUSH, val, info=info)
def CHAR(val: int, info=None)    -> Token: return Token(OpTypes.OP_CHAR, val, info=info)
def STRING(val: str, info=None)  -> Token: return Token(OpTypes.OP_STRING, val, info=info)
def BOOL(val: bool, info=None)   -> Token: return Token(OpTypes.OP_BOOL, val, info=info)
def WORD(val: str, info=None)    -> Token: return Token(OpTypes.OP_WORD, val, info=info)
def DROP(info=None)              -> Token: return Token(Intrinsics.OP_DROP, info=info)
def DUP(info=None)               -> Token: return Token(Intrinsics.OP_DUP, info=info)
def DUP2(info=None)              -> Token: return Token(Intrinsics.OP_DUP2, info=info)
def SWAP(info=None)              -> Token: return Token(Intrinsics.OP_SWAP, info=info)
def SWAP2(info=None)             -> Token: return Token(Intrinsics.OP_SWAP2, info=info)
def OVER(info=None)              -> Token: return Token(Intrinsics.OP_OVER, info=info)
def ROT(info=None)               -> Token: return Token(Intrinsics.OP_ROT, info=info)
def RROT(info=None)              -> Token: return Token(Intrinsics.OP_RROT, info=info)

def PLUS(info=None)              -> Token: return Token(Operands.OP_PLUS, info=info)
def MINUS(info=None)             -> Token: return Token(Operands.OP_MINUS, info=info)
def MUL(info=None)               -> Token: return Token(Operands.OP_MUL, info=info)
def DIV(info=None)               -> Token: return Token(Operands.OP_DIV, info=info)
def MOD(info=None)               -> Token: return Token(Operands.OP_MOD, info=info)
def DIVMOD(info=None)            -> Token: return Token(Operands.OP_DIVMOD, info=info)
def INCREMENT(info=None)         -> Token: return Token(Operands.OP_INCREMENT, info=info)
def DECREMENT(info=None)         -> Token: return Token(Operands.OP_DECREMENT, info=info)

def OP_BLSH(info=None)           -> Token: return Token(Operands.OP_BLSH, info=info)
def OP_BRSH(info=None)           -> Token: return Token(Operands.OP_BRSH, info=info)
def OP_BAND(info=None)           -> Token: return Token(Operands.OP_BAND, info=info)
def OP_BOR(info=None)            -> Token: return Token(Operands.OP_BOR, info=info)
def OP_BXOR(info=None)           -> Token: return Token(Operands.OP_BXOR, info=info)

def EQ(info=None)                -> Token: return Token(Operands.OP_EQ, info=info)
def NE(info=None)                -> Token: return Token(Operands.OP_NE, info=info)
def GT(info=None)                -> Token: return Token(Operands.OP_GT, info=info)
def GE(info=None)                -> Token: return Token(Operands.OP_GE, info=info)
def LT(info=None)                -> Token: return Token(Operands.OP_LT, info=info)
def LE(info=None)                -> Token: return Token(Operands.OP_LE, info=info)

def DUMP(info=None)              -> Token: return Token(OpTypes.OP_DUMP, info=info)
def UDUMP(info=None)             -> Token: return Token(OpTypes.OP_UDUMP, info=info)
def CDUMP(info=None)             -> Token: return Token(OpTypes.OP_CDUMP, info=info)
def HEXDUMP(info=None)           -> Token: return Token(OpTypes.OP_HEXDUMP, info=info)

def SYSCALL(info=None)           -> Token: return Token(OpTypes.OP_SYSCALL, info=info)
def SYSCALL1(info=None)          -> Token: return Token(OpTypes.OP_SYSCALL1, info=info)
def SYSCALL2(info=None)          -> Token: return Token(OpTypes.OP_SYSCALL2, info=info)
def SYSCALL3(info=None)          -> Token: return Token(OpTypes.OP_SYSCALL3, info=info)
def SYSCALL4(info=None)          -> Token: return Token(OpTypes.OP_SYSCALL4, info=info)
def SYSCALL5(info=None)          -> Token: return Token(OpTypes.OP_SYSCALL5, info=info)
def SYSCALL6(info=None)          -> Token: return Token(OpTypes.OP_SYSCALL6, info=info)

def RSYSCALL1(info=None)         -> Token: return Token(OpTypes.OP_RSYSCALL1, info=info)
def RSYSCALL2(info=None)         -> Token: return Token(OpTypes.OP_RSYSCALL2, info=info)
def RSYSCALL3(info=None)         -> Token: return Token(OpTypes.OP_RSYSCALL3, info=info)
def RSYSCALL4(info=None)         -> Token: return Token(OpTypes.OP_RSYSCALL4, info=info)
def RSYSCALL5(info=None)         -> Token: return Token(OpTypes.OP_RSYSCALL5, info=info)
def RSYSCALL6(info=None)         -> Token: return Token(OpTypes.OP_RSYSCALL6, info=info)

def IF(info=None)                -> Token: return Token(FlowControl.OP_IF, info=info)
def ELIF(info=None)              -> Token: return Token(FlowControl.OP_ELIF, info=info)
def ELSE(info=None)              -> Token: return Token(FlowControl.OP_ELSE, info=info)
def WHILE(info=None)             -> Token: return Token(FlowControl.OP_WHILE, info=info)
def DO(info=None)                -> Token: return Token(FlowControl.OP_DO, info=info)
def END(info=None)               -> Token: return Token(FlowControl.OP_END, info=info)
def LABEL(name, info=None)       -> Token: return Token(FlowControl.OP_LABEL, name, info=info)
def LET(info=None)               -> Token: return Token(FlowControl.OP_LET, info=info)
def WITH(info=None)              -> Token: return Token(FlowControl.OP_WITH, info=info)

def ARGC(info=None)              -> Token: return Token(Intrinsics.OP_ARGC, info=info)
def ARGV(info=None)              -> Token: return Token(Intrinsics.OP_ARGV, info=info)

def LOAD(info=None)              -> Token: return Token(OpTypes.OP_LOAD, info=info)
def LOAD16(info=None)            -> Token: return Token(OpTypes.OP_LOAD16, info=info)
def LOAD32(info=None)            -> Token: return Token(OpTypes.OP_LOAD32, info=info)
def LOAD64(info=None)            -> Token: return Token(OpTypes.OP_LOAD64, info=info)

def STORE(info=None)             -> Token: return Token(OpTypes.OP_STORE, info=info)
def STORE16(info=None)           -> Token: return Token(OpTypes.OP_STORE16, info=info)
def STORE32(info=None)           -> Token: return Token(OpTypes.OP_STORE32, info=info)
def STORE64(info=None)           -> Token: return Token(OpTypes.OP_STORE64, info=info)

def EXIT(info=None) -> Token: return Token(OpTypes.OP_EXIT, info=info)

def MACRO(info=None)             -> Token: return Token(PreprocTypes.MACRO, info=info)
def CALL(val: str, info=None)    -> Token: return Token(PreprocTypes.CALL, val, info=info)
def PROC(info=None)              -> Token: return Token(PreprocTypes.PROC, info=info)
def IN(info=None)                -> Token: return Token(PreprocTypes.IN, info=info)
def OUT(info=None)               -> Token: return Token(PreprocTypes.OUT, info=info)
def MEMORY(info=None)            -> Token: return Token(PreprocTypes.MEMORY, info=info)
def PUSHMEMORY(val, info=None)   -> Token: return Token(OpTypes.OP_PUSHMEMORY, val, info=info)
def INCLUDE(info=None)           -> Token: return Token(PreprocTypes.INCLUDE, info=info)
def CAST(val: Type, info=None)   -> Token: return Token(PreprocTypes.CAST, val, info=info)

KEYWORDS = {
	"true":      (lambda val, info: BOOL(True, info=info)),
	"false":     (lambda val, info: BOOL(False, info=info)),
	"dump":      (lambda val, info: DUMP(info=info)),
	"udump":     (lambda val, info: UDUMP(info=info)),
	"blsh":      (lambda val, info: OP_BLSH(info=info)),
	"brsh":      (lambda val, info: OP_BRSH(info=info)),
	"band":      (lambda val, info: OP_BAND(info=info)),
	"bor":       (lambda val, info: OP_BOR(info=info)),
	"bxor":      (lambda val, info: OP_BXOR(info=info)),
	"cdump":     (lambda val, info: CDUMP(info=info)),
	"hexdump":   (lambda val, info: HEXDUMP(info=info)),
	"syscall":   (lambda val, info: SYSCALL(info=info)),
	"syscall1":  (lambda val, info: SYSCALL1(info=info)),
	"syscall2":  (lambda val, info: SYSCALL2(info=info)),
	"syscall3":  (lambda val, info: SYSCALL3(info=info)),
	"syscall4":  (lambda val, info: SYSCALL4(info=info)),
	"syscall5":  (lambda val, info: SYSCALL5(info=info)),
	"syscall6":  (lambda val, info: SYSCALL6(info=info)),
	"rsyscall1": (lambda val, info: RSYSCALL1(info=info)),
	"rsyscall2": (lambda val, info: RSYSCALL2(info=info)),
	"rsyscall3": (lambda val, info: RSYSCALL3(info=info)),
	"rsyscall4": (lambda val, info: RSYSCALL4(info=info)),
	"rsyscall5": (lambda val, info: RSYSCALL5(info=info)),
	"rsyscall6": (lambda val, info: RSYSCALL6(info=info)),
	"drop":      (lambda val, info: DROP(info=info)),
	"dup":       (lambda val, info: DUP(info=info)),
	"dup2":      (lambda val, info: DUP2(info=info)),
	"swap":      (lambda val, info: SWAP(info=info)),
	"swap2":     (lambda val, info: SWAP2(info=info)),
	"over":      (lambda val, info: OVER(info=info)),
	"rot":       (lambda val, info: ROT(info=info)),
	"rrot":      (lambda val, info: RROT(info=info)),
	"exit":      (lambda val, info: EXIT(info=info)),
	"if":        (lambda val, info: IF(info=info)),
	"elif":      (lambda val, info: ELIF(info=info)),
	"else":      (lambda val, info: ELSE(info=info)),
	"while":     (lambda val, info: WHILE(info=info)),
	"do":        (lambda val, info: DO(info=info)),
	"macro":     (lambda val, info: MACRO(info=info)),
	"proc":      (lambda val, info: PROC(info=info)),
	"in":        (lambda val, info: IN(info=info)),
	"out":       (lambda val, info: OUT(info=info)),
	"memory":    (lambda val, info: MEMORY(info=info)),
	"include":   (lambda val, info: INCLUDE(info=info)),
	"end":       (lambda val, info: END(info=info)),
	"let":       (lambda val, info: LET(info=info)),
	"with":      (lambda val, info: WITH(info=info)),
	"argc":      (lambda val, info: ARGC(info=info)),
	"argv":      (lambda val, info: ARGV(info=info)),
	"store":     (lambda val, info: STORE(info=info)),
	"load":      (lambda val, info: LOAD(info=info)),
}


OPERANDS = {
	"+":    (lambda val, info: PLUS(info=info)),
	"-":    (lambda val, info: MINUS(info=info)),
	"*":    (lambda val, info: MUL(info=info)),
	"/":    (lambda val, info: DIV(info=info)),
	"%":    (lambda val, info: MOD(info=info)),
	"/%":   (lambda val, info: DIVMOD(info=info)),
	"++":   (lambda val, info: INCREMENT(info=info)),
	"--":   (lambda val, info: DECREMENT(info=info)),
	"==":   (lambda val, info: EQ(info=info)),
	"!=":   (lambda val, info: NE(info=info)),
	">":    (lambda val, info: GT(info=info)),
	">=":   (lambda val, info: GE(info=info)),
	"<":    (lambda val, info: LT(info=info)),
	"<=":   (lambda val, info: LE(info=info)),

	"!":    (lambda val, info: STORE(info=info)),
	"!16":  (lambda val, info: STORE16(info=info)),
	"!32":  (lambda val, info: STORE32(info=info)),
	"!64":  (lambda val, info: STORE64(info=info)),

	"@":    (lambda val, info: LOAD(info=info)),
	"@16":  (lambda val, info: LOAD16(info=info)),
	"@32":  (lambda val, info: LOAD32(info=info)),
	"@64":  (lambda val, info: LOAD64(info=info)),

	"<<":   (lambda val, info: OP_BLSH(info=info)),
	">>":   (lambda val, info: OP_BRSH(info=info)),
	"&":    (lambda val, info: OP_BAND(info=info)),
	"|":    (lambda val, info: OP_BOR(info=info)),
	"^":    (lambda val, info: OP_BXOR(info=info)),
	"^":    (lambda val, info: OP_BXOR(info=info)),
}


class NoEngine(Exception): pass
class MakeException(Exception): pass
class NASMException(Exception): pass
class LinkerException(Exception): pass

def StrToType(s: str) -> Type | None:
	t, l = {
		'any':   (Types.ANY, 3),
		'void':  (Types.ANY, 4),
		'int':   (Types.INT, 3),
		'ptr':   (Types.PTR, 3),
		'bool':  (Types.BOOL, 4),
		'char':  (Types.CHAR, 4),

		'byte':  (Types.CHAR, 4),
		'dword': (Types.INT, 4),
	}.get(s.rstrip('*'), None)
	if t is None: return None

	while s[l:] and s[l:][0] == '*':
		t = Types.PTR[t]
		l += 1
	return t

def unescape_string(s):
	return s.encode('latin-1', 'backslashreplace').decode('unicode-escape')

def procedureFactory(token: Token, name: Token, args: list[Token], out: list[Token], body: list[Token]) -> Procedure:
	l = []
	try:
		for var, typ in batched(args, 2):
			assert var.type == OpTypes.OP_WORD, var
			assert typ.type == PreprocTypes.CAST, typ
			l.append((var, typ.value))
	except AssertionError as e:
		raise InvalidSyntax(e.args[0].info, 'Invalid procedure argument syntax')
	except:
		raise InvalidSyntax(token.info, 'Invalid procedure argument syntax')
	m = []
	for tok in out:
		if tok.type == PreprocTypes.CAST:
			m.append((tok, tok.value))
		else:
			raise InvalidSyntax(tok.info, 'Invalid procedure return syntax')
	return Procedure(token,
				token.value.end,
				name.value,
				l,
				m,
				body)


class Program(AbstractProgram):
	def __init__(self, path: str | Path, engine: Optional[Engine]=None, includes: Optional[list[str | Path]]=None):
		self.instructions: list[Token] = []
		self.engine: Optional[Engine] = engine
		self.path: Path = Path(path)
		self.pointer = 0
		self.symbols: dict[str, Symbol] = {}
		self.globals: dict[str, Symbol] = {}
		self.let_depth = 0
		self._in_preproc = 0
		self._position = 0
		self.includes: list[Path] = [self.path.parent, Path(os.getcwd()), Path(__file__).parent] + ([Path(i) for i in includes] if includes else [])

	def match_word(self, token: TokenInfo) -> list[Token]:
		if token.string in self.symbols:
			if self.symbols[token.string].type == PreprocTypes.MEMORY:
				return [self.symbols[token.string].data]
			elif self.symbols[token.string].type == PreprocTypes.PROC:
				return [CALL(token.string, info=token)]
			elif self.symbols[token.string].type == PreprocTypes.MACRO:
				return [LABEL(name=token.string, info=token), *[i.copy(token) for i in self.symbols[token.string].data]]
		return [WORD(val=token.string, info=token)]

	def match_token(self, token: TokenInfo) -> list[Token]:
		if token.type == TokenTypes.NUMBER:
			return [PUSH(int(token.string), info=token)]
		if token.type == TokenTypes.CHAR:
			return [CHAR(ord(unescape_string(token.string)), info=token)]
		if token.type == TokenTypes.STRING:
			return [STRING(unescape_string(token.string), info=token)]
		if token.type == TokenTypes.WORD and token.string in KEYWORDS:
			return [KEYWORDS[token.string](token.string, token)]
		if token.type == TokenTypes.OP and token.string == '//':
			raise self.Comment()
		if token.type == TokenTypes.OP and token.string != '//':
			if token.string not in OPERANDS:
				raise UnknownToken(token, "Is not a recognized symbol")
			return [OPERANDS[token.string](token.string, token)]
		if token.type == TokenTypes.WORD and token.string not in KEYWORDS:
			return self.match_word(token)
		if token.type == TokenTypes.NEW_LINE:
			raise self.EndLine()
		if token.type == TokenTypes.CAST:
			t = StrToType(token.string)
			if t is None:
				raise InvalidType(token, f"{token.string} is not a recognized type") # TODO 'did you mean + levenshtein distance'
			return [CAST(t, info=token)]
		raise UnknownToken(token, "Is not a recognized symbol")

	@classmethod
	def frombuffer(cls, buffer: TextIO, path: str | Path, includes: list[str | Path], *, debug=False) -> 'Program':
		tokenizer = Tokenize(buffer, debug=debug)

		self = cls(path=path, includes=includes)
		self.parse_tokens(tokenizer, debug=debug)
		return self

	
	def build_tokens(self, debug=False):
		comment = -1
		while True:
			token = (yield)
			if token is None:
				break
			if token.start[0] == comment: continue
			try:
				tokens = self.match_token(token)
				if self._in_preproc:
					self._in_preproc += 1
				for index, t in enumerate(tokens):
					if debug:
						print(t)
					self.add(t)
				yield iter(tokens)
			except self.Comment as e: comment = token.start[0]
			except self.EndLine as e: pass

	def parse_tokens(self, tokenizer: Tokenize, *, debug=False) -> 'Program':
		build_tokens = self.build_tokens(debug)
		flow_control = self.process_flow_control()
		expand = self.expand()

		next(build_tokens)
		next(flow_control)
		next(expand)
		for t in tokenizer:
			tokens = build_tokens.send(t)
			if tokens is None:
				continue

			next(build_tokens)
			for token in tokens:
				flow_control.send(token)
				ex = expand.send(token)
				if ex:
					tokenizer.extend(ex)
				next(expand)

		flow_control.send(None)

		for index, token in enumerate(self.instructions):
			token.position = index
			
		return self

	def search_path(self, path, query):
		if not path:
			raise FileNotFoundError()
		try:
			return open(Path(path[0]) / query, 'r')
		except:
			return self.search_path(path[1:], query)

	def expand(self):
		prev = None
		while True:
			token = (yield)
			match (prev, token):
				case (Token(type=PreprocTypes.INCLUDE), Token(type=OpTypes.OP_STRING, value=file)):
					self.instructions.pop(-1)
					self.instructions.pop(-1)
					self._position -= 2
					try:
						yield iter(Tokenize(self.search_path(self.includes, file), close=True, parent=token.info))
					except FileNotFoundError:
						raise FileError(token.info, f"No file `{token.value}`")

				case (Token(type=PreprocTypes.INCLUDE), any):
					raise InvalidSyntax(any.info, "`include` requires a string")
					
				case _:
					yield None

			prev = token

	def parse_macro(self, tokens: list[Token]):
		assert tokens[1].info is not None

		if len(tokens) == 1:
			raise InvalidSyntax(tokens[0].info, "`macro` requires a name")
		if tokens[1].type != OpTypes.OP_WORD:
			raise InvalidSyntax(tokens[1].info, f"`macro` name must be a word not `{tokens[1].type.name}`")
		if tokens[1].info.string in self.symbols:
			raise SymbolRedefined(tokens[1].info, "Has already been defined")
			
		self.symbols[tokens[1].info.string] = Symbol(PreprocTypes.MACRO, tokens[2:])

	def parse_proc(self, root: Token, end: Token):
		in_ = root.value.next
		out_ = in_.value.next

		s, e = root.position+1, root.position
		args = []
		out = []
		# TODO actually choose whether the minimal syntax is
		#	proc name in end
		# 	or
		# 	proc name end
		if in_:
			s, e = e+1, in_.position
			args = self.instructions[s:e]
		if out_:
			s, e = e+1, out_.position
			out = self.instructions[s:e]
		s, e = e+1, end.position
		body = self.instructions[s:e]
		if len(args) < 1:
			raise InvalidSyntax(root.info, "`proc` requires a name")
		if args[0].type == PreprocTypes.CALL:
			raise SymbolRedefined(args[0].info, "Has already been defined")
		if args[0].type != OpTypes.OP_WORD:
			raise InvalidSyntax(args[0].info, f"`proc` name must be a word not `{args[0].type.name}`")
		assert args[0].info
		if args[0].info.string in self.symbols:
			raise SymbolRedefined(args[0].info, "Has already been defined")
			
		name = args[0].info.string
		in_.value.data = args
		root.value.data = body

		root.value = procedureFactory(root, args[0], args[1:], out, body)

		for i in reversed(range(root.position+1, s)):
			self.instructions.pop(i)
			self._position -= 1

		self.symbols[name] = Symbol(PreprocTypes.PROC, root)

		for i, e in enumerate(root.value.body):
			if e.type == OpTypes.OP_WORD and e.value == name:
					root.value.body[i] = CALL(e.info.string, info=e.info)

	def parse_memory(self, tokens: list[Token]):
		assert tokens[1].info
		assert isinstance(tokens[0].value, FlowInfo)

		if len(tokens) == 1:
			raise InvalidSyntax(tokens[0].info, "`memory` requires a name")
		if tokens[1].type != OpTypes.OP_WORD:
			raise InvalidSyntax(tokens[1].info, f"`memory` name must be a word not `{tokens[1].type.name}`")
		if tokens[1].info.string in self.symbols:
			raise SymbolRedefined(tokens[1].info, "Has already been defined")

		tokens[0].value.data = tokens[1:]
		self.symbols[tokens[1].info.string] = Symbol(PreprocTypes.MEMORY, tokens[0])
		self.globals[tokens[1].info.string] = self.symbols[tokens[1].info.string]

	def process_flow_control(self):
		stack: list[tuple[Token, FlowInfo]] = []

		while True:
			token = (yield)
			if token is None:
				break
			match token:
				case Token(type=FlowControl.OP_IF):
					token.value = FlowInfo(token)
					stack.append((token, token.value))

				case Token(type=FlowControl.OP_ELIF):
					try:
						top, flow = stack.pop()
					except:
						raise InvalidSyntax(token.info, '`elif` must be preceded by `if` or `elif`')
					if top.type not in (FlowControl.OP_IF, FlowControl.OP_ELIF):
						raise InvalidSyntax(top.info, '`elif` must be preceded by `if` or `elif`')
						raise Reporting(token.info, "", InvalidSyntax(top.info, 'missing a `do` before starting `elif`'))
					token.value = FlowInfo(root=flow.root, prev=top)
					flow.next = token
					stack.append((token, token.value))

				case Token(type=FlowControl.OP_ELSE):
					try:
						top, flow = stack.pop()
					except:
						raise InvalidSyntax(token.info, '`else` must be preceded by `if` or `elif`')
					if top.type not in (FlowControl.OP_IF, FlowControl.OP_ELIF):
						raise InvalidSyntax(top.info, '`else` must be preceded by `if` or `elif`')
					token.value = FlowInfo(root=flow.root, prev=top)
					flow.next = token
					stack.append((token, token.value))

				case Token(type=FlowControl.OP_END):
					try:
						top, flow = stack.pop()
					except:
						raise InvalidSyntax(token.info, '`end` token without block start')

					token.value = FlowInfo(root=flow.root, prev=top)
					if top.type is PreprocTypes.MACRO:
						self.parse_macro(self.instructions[flow.root.position:token.position])
						for i in reversed(range(top.position, token.position+1)):
							self.instructions.pop(i)
							self._position -= 1
						self._in_preproc = 0
					elif top.type in [PreprocTypes.PROC, PreprocTypes.IN, PreprocTypes.OUT]:
						top = top.value.root
						flow = top.value
						flow.end = token

						assert flow.next
						self.parse_proc(top, token)
						proc = top.value
						self._in_preproc = 0

					elif top.type is PreprocTypes.MEMORY:
						self.parse_memory(self.instructions[flow.root.position:token.position])
						for i in reversed(range(top.position, token.position+1)):
							self.instructions.pop(i)
							self._position -= 1
						self._in_preproc = 0
					elif top.type in [FlowControl.OP_LET, FlowControl.OP_WITH]:
						self.let_depth -= 1
						if self._in_preproc:
							continue
						assert flow.next
						assert flow.next
						words = self.instructions[flow.root.position+1:flow.next.position]
						top.value.data = words
						for i in reversed(range(top.position+1, top.value.next.position)):
							self.instructions.pop(i)
							self._position -= 1
					else:
						node = token
						haselse = False
						while node:
							if node.type == FlowControl.OP_ELSE:
								haselse = True
							node.value.haselse = haselse
							node.value.end = token
							node = node.value.prev

				case Token(type=FlowControl.OP_WHILE):
					token.value = FlowInfo(token)
					stack.append((token, token.value))

				case Token(type=FlowControl.OP_DO):
					try:
						top, flow = stack.pop()
					except:
						raise InvalidSyntax(token.info, "`do` must be preceded by an `if`, `elif`, `while`, `let` or with")
					if top.type not in [FlowControl.OP_IF, FlowControl.OP_ELIF, FlowControl.OP_WHILE, FlowControl.OP_LET, FlowControl.OP_WITH]:
						raise InvalidSyntax(token.info, "`do` must be preceded by an `if`, `elif`, `while`, `let` or with")
					token.value = flow
					if top.type in [FlowControl.OP_LET, FlowControl.OP_WITH]:
						flow.next = token
					stack.append((top, flow))
					
				case Token(type=FlowControl.OP_LET):
					token.value = FlowInfo(token)
					stack.append((token, token.value))
					self.let_depth += 1

				case Token(type=FlowControl.OP_WITH):
					token.value = FlowInfo(token)
					stack.append((token, token.value))
					self.let_depth += 1

				case Token(type=PreprocTypes.MACRO):
					token.value = FlowInfo(token)
					if self._in_preproc:
						raise InvalidSyntax(token.info, f"nested macro definition is not allowed")
					self._in_preproc = 1
					stack.append((token, token.value))

				case Token(type=PreprocTypes.IN, value=val):
					try:
						top, flow = stack.pop()
					except:
						raise InvalidSyntax(token.info, "`in` must be preceded by `proc`")
					if top.type not in [PreprocTypes.PROC]:
						raise InvalidSyntax(token.info, "`in` must be preceded by `proc`")
					self._in_preproc = 0
					token.value = FlowInfo(flow.root, top)
					flow.next = token
					stack.append((token, token.value))

				case Token(type=PreprocTypes.OUT, value=val):
					try:
						top, flow = stack.pop()
					except:
						raise InvalidSyntax(token.info, "`out` must be preceded by `proc` or `in`")
					if top.type not in [PreprocTypes.PROC, PreprocTypes.IN]:
						raise InvalidSyntax(token.info, "`out` must be preceded by `proc` or `in`")
					self._in_preproc = 0
					token.value = FlowInfo(flow.root, top)
					flow.next = token
					stack.append((token, token.value))

				case Token(type=PreprocTypes.PROC, value=val):
					if val is not None:
						continue
					token.value = FlowInfo(token)
					if self._in_preproc:
						raise InvalidSyntax(token.info, f"nested proc definition is not allowed")
					self._in_preproc = 1
					stack.append((token, token.value))

				case Token(type=PreprocTypes.MEMORY, value=val):
					if val is not None:
						continue
					token.value = FlowInfo(token)
					if self._in_preproc:
						raise InvalidSyntax(token.info, f"nested memory definition is not allowed")
					self._in_preproc = 1
					stack.append((token, token.value))

		if stack:
			raise InvalidSyntax(stack[-1][0].info, "is missing an end")
		yield

	def add(self, token: Token) -> 'Program':
		self.instructions.append(token)
		token.position = self._position
		self._position += 1
		return self

	def run(self) -> int:
		assert len(self.instructions) != 0, "Empty program"

		if self.engine is None:
			raise NoEngine("Add engine before running")
		self.engine.before(self)
		skip = 0
		while self.pointer < len(self.instructions):
			try:
				self.pointer += self.engine.step(self.instructions[self.pointer]) + 1
			except Engine.ExitFromEngine as e:
				self.engine.close(self)
				return e.args[0]
		self.engine.close(self)
		if self.engine.exited == False:
			raise InvalidSyntax(self.instructions[-1].info, "Program was not exited properly")
		return 0

def callcmd(cmd, verbose=False, devnull=True):
	if verbose:
		print("CMD:", cmd)
	if devnull:
		return subprocess.call(cmd, stdout=subprocess.DEVNULL)
	else:
		return subprocess.call(cmd)

def fclean(*, verbose=False):
	objs = Path("objs")
	if verbose:
		print("rm -rf objs")
	try:
		shutil.rmtree(objs)
	except FileNotFoundError:
		pass
	callcmd(["make", "-C", "src/cfunc/", "fclean"], verbose=verbose)



def compile(*, source: str | Path,
		 output: str | Path | TextIO,
		 temp: str | Path,
		 verbose: bool=False,
		 includes: list[str],
		 execution: bool=False,
		 argv: list[str],) -> int:
	with open(source, 'r') as f:
		try:
			p = Program.frombuffer(f, debug=False, path=source, includes=[Path(i) for i in includes])
		except LangExceptions as e:
			trace(e)
			return -1
		except Stopped as e:
			return -1

	objs = Path(temp)
	if not objs.exists():
		objs.mkdir()

	with open(objs / "intermediary.asm", 'w') as f:
		p.engine = Compiler(f)
		try:
			code = p.run()

		except LangExceptions as e:
			trace(e)
			return -1

	if e:=callcmd(["make", "-C", "src/cfunc/"], verbose=verbose, devnull=True):
		raise MakeException(e)
	if e:=callcmd(["nasm", "-g", "-f", "elf64", "objs/intermediary.asm", "-o", "objs/intermediary.o"], verbose=verbose, devnull=True):
		raise NASMException(e)
	if e:=callcmd(["ld",
				"src/cfunc/objs/dump.o",
				"src/cfunc/objs/memory.o",
				"objs/intermediary.o",
				"-lc",
				"-I", "/lib64/ld-linux-x86-64.so.2",
				"-o", output ], verbose=verbose, devnull=True):
		raise LinkerException(e)

	if execution:
		return callcmd([f"./{output}", *argv], verbose=verbose, devnull=False)
	else:
		return code
	return 0

def interpret(*, source: str | Path,
		 includes: list[str],
		 argv: list[str],
		 output: str | Path | BinaryIO) -> int:

	with open(source, 'r') as f:
		try:
			p = Program.frombuffer(f, debug=False, path=source, includes=[Path(i) for i in includes])
		except LangExceptions as e:
			trace(e)
			return -1
		except Stopped as e:
			return -1

	if output == 'stdout':
		output = sys.stdout.buffer
	try:
		if isinstance(output, (str, Path)):
			with open(output, 'wb') as f:
				p.engine = Interpreter(f)
				p.engine.setargv(argv)
				code = p.run()
		else:
			p.engine = Interpreter(output)
			p.engine.setargv(argv)
			code = p.run()

	except LangExceptions as e:
		trace(e)
		return -1
	return code
