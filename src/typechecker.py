from .classes import (
	Token,
	Type,
	Procedure,
	FlowInfo,
)

from .lexer import (
	FlowControl,
	TypesType,
	OpTypes,
	Intrinsics,
	Operands,
	PreprocTypes,
)

from .errors import (
	LangExceptions,
	UnknownToken,
	InvalidSyntax,
	Reporting,
	NotEnoughTokens,
	InvalidType,
	TypeCheckerException,
	MissingToken,
	AddedToken,
	StackNotEmpty,
	ProcedureError,

	BlockException,
	IfException,
	ElifException,
	ElseException,
	WhileException,
)

from enum import Enum, auto
from dataclasses import dataclass
from typing import ClassVar
from copy import deepcopy

ANY		= Type('ANY', 8)
CHAR	= Type('CHAR', 1)
INT		= Type('INT', 8)
PTR		= Type('PTR', 8)
BOOL	= Type('BOOL', 4)

class Types:
	ANY		= ANY
	CHAR	= CHAR
	INT		= INT
	PTR		= PTR
	BOOL	= BOOL

def derefType(t: Type) -> Type:
	t2 = deepcopy(t)
	n = t2
	p = n
	while n.parent is not None:
		p = n
		n = n.parent
	if p == n:
		raise ValueError("Can't be deref'ed")
	p.parent = None
	return t2

def getOperationName(t: Token):
	return t.type.name
#	n = t.type.name.lower()
#	if n.startswith('op_'):
#		return n[3:]
#	return n

def getTypeName(t):
	return repr(t)

def TypeChecker():
	c = _TypeChecker()
	return iter(c), c

def run_single(token: Token, stack: list[tuple[Token, Type]]):
	return _TypeChecker.run_single(token, stack)
		

class _TypeChecker:
	def __init__(self):
		self.stack: list[tuple[Token, Type]] = []
		self.block_stack: list[list[tuple[Token, Type]]] = []
		self.block_origin_stack: list[list[tuple[Token, Type]]] = []
		self.locals: list[dict[str, tuple[Token, Type]]] = []
		self.procedures: dict[str, Procedure] = {}
		self.block_exit = False
		self.last_case = -1

	def __iter__(self):
		c = self.run()
		next(c)
		return c

	def check_length(self, n: int, token: Token):
		if len(self.stack) < n:
			raise NotEnoughTokens(token.info, f"Not enough arguments for {getOperationName(token)}")

	def size_check(self, expected: int, token: Token) -> tuple[Token, Type]:
		a_token, a_type = self.stack.pop()
		if a_type.size != expected:
			raise Reporting(a_token.info, f"{getTypeName(a_type)} has a byte side of {a_type.size}, expected {expected}", InvalidType(token.info, f"invalid size for {getOperationName(token)}"))
		return a_token, a_type

	def type_check(self, expected: Type, token: Token, *, consume=True) -> tuple[Token, Type]:
		if consume:
			a_token, a_type = self.stack.pop()
		else:
			a_token, a_type = self.stack[-1]
		if expected == ANY:
			return a_token, a_type
		if a_type != expected:
			raise Reporting(a_token.info, f"{getTypeName(a_type)} must be {getTypeName(expected)}", InvalidType(token.info, f"invalid type for {getOperationName(token)}"))
		return a_token, a_type

	def check_same(self, length: int, token: Token) -> Type:
		self.check_length(length, token)
		a_token, expected = self.stack.pop()
		for i in range(1, length):
			b_token, b_type = self.stack.pop()
			if b_type != expected:
				raise Reporting(b_token.info, f"{getTypeName(b_type)} must be equal to {getTypeName(expected)}", Reporting(a_token.info, f"{getTypeName(expected)} and", InvalidType(token.info, f"invalid type for {getOperationName(token)}")))
		return expected
		

	def check(self, args: list[Type], token: Token, *, consume=True) -> list[tuple[Token, Type]]:
		self.check_length(len(args), token)
		stack_types = []
		for i in args:
			stack_types.append(self.type_check(i, token, consume=consume))
		return stack_types

	def check_comb(self, args: list[list[Type]], token) -> tuple[int, list[Type]]:
		assert len(args) != 0
		lengths = [*map(len, args)]
		assert len(set(lengths)) == 1,"All cases must be of the same length"
		length = lengths[0]

		valid = [True for _ in args]
		self.check_length(length, token)
		stack_types = []
		for index, types in enumerate(zip(*args)):
			stack_token, stack_type = self.stack.pop()
			stack_types.append(stack_type)
			hit = False
			new = valid[:]
			for i,_ in filter(lambda x: x[1], enumerate(valid)):
				if types[i] == stack_type:
					hit = True
				else:
					new[i] = False
			if not hit:
				*choices ,= filter(lambda x: x[1], zip(types, valid))
				msg = f"{getTypeName(stack_type)} expected to be {' or '.join(getTypeName(i) for i, _ in set(choices))}"
				raise InvalidType(stack_token.info, msg, TypeCheckerException(token.info, f"invalid type for {getOperationName(token)}"))
			valid = new
		return next(filter(lambda x: x[1], enumerate(valid)))[0], stack_types

	def cmp_stack(self, stack, prev, block: BlockException):
		if len(stack) > len(prev):
			raise AddedToken(stack[-1][0].info, "was added", block)
		if len(stack) < len(prev):
			raise MissingToken(prev[-1][0].info, "is missing", block)
		for i, j in zip(prev, stack):
			if i[1] != j[1]:
				raise Reporting(j[0].info, "", Reporting(i[0].info, "got changed by", block))

	@property
	def last_type(self) -> Type | None:
		if self.stack:
			return self.stack[-1][1]
		return None

	@classmethod
	def run_single(cls, token: Token, stack: list[tuple[Token, Type]]):
		c = cls()
		c.stack = stack
		c.block_stack = [stack]
		i = iter(c)
		i.send(token)
		return c.last_case, c.stack, c.last_type
		
	def run(self):
		while True:
			token = (yield)
			self.last_case = -1
			if token is None:
				break
			match token:
				case Token(type=FlowControl.OP_LABEL, value=val):
					pass

				case Token(type=OpTypes.OP_PUSH, value=val):
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_BOOL, value=val):
					self.stack.append((token, BOOL))

				case Token(type=OpTypes.OP_CHAR, value=val):
					self.stack.append((token, CHAR))

				case Token(type=OpTypes.OP_STRING, value=val):
					self.stack.append((token, INT))
					self.stack.append((token, PTR[CHAR]))

				case Token(type=Intrinsics.OP_DROP, value=val):
					self.check([ANY], token)

				case Token(type=Intrinsics.OP_DUP, value=val):
					self.check_length(1, token)
					a = self.stack.pop()
					self.stack.append(a)
					self.stack.append((token, a[1]))

				case Token(type=Intrinsics.OP_DUP2, value=val):
					self.check_length(2, token)
					a = self.stack.pop()
					b = self.stack.pop()
					self.stack.append(b)
					self.stack.append(a)
					self.stack.append((token, b[1]))
					self.stack.append((token, a[1]))

				case Token(type=Intrinsics.OP_SWAP, value=val):
					self.check_length(2, token)
					a = self.stack.pop()
					b = self.stack.pop()
					self.stack.append(a)
					self.stack.append(b)

				case Token(type=Intrinsics.OP_SWAP, value=val):
					self.check_length(4, token)
					a = self.stack.pop()
					b = self.stack.pop()
					c = self.stack.pop()
					d = self.stack.pop()
					self.stack.append(c)
					self.stack.append(d)
					self.stack.append(a)
					self.stack.append(b)

				# d c b a 
				# b a d c 
				case Token(type=Intrinsics.OP_OVER, value=val):
					self.check_length(2, token)
					self.stack.append(self.stack[-2])

				case Token(type=Intrinsics.OP_ROT, value=val):
					self.check_length(3, token)
					a = self.stack.pop(-1)
					b = self.stack.pop(-1)
					c = self.stack.pop(-1)
					self.stack.append(b)
					self.stack.append(a)
					self.stack.append(c)

				case Token(type=Intrinsics.OP_RROT, value=val):
					self.check_length(3, token)
					a = self.stack.pop(-1)
					b = self.stack.pop(-1)
					c = self.stack.pop(-1)
					self.stack.append(a)
					self.stack.append(c)
					self.stack.append(b)

				case Token(type=Operands.OP_PLUS, value=val):
					case, stack_types = self.check_comb([
						[INT,INT],
						[INT,PTR[ANY]],
						[PTR[ANY],INT],
						[CHAR, CHAR],
					], token)
					assert case != -1 and case < 4, "???"
					if case == 0: self.stack.append((token, INT))
					if case == 1: self.stack.append((token, stack_types[1]))
					if case == 2: self.stack.append((token, stack_types[0]))
					if case == 3: self.stack.append((token, CHAR))
					self.last_case = case

				case Token(type=Operands.OP_MINUS, value=val):
					case, stack_types = self.check_comb([
						[INT,INT],
						[INT,PTR[ANY]],
						[PTR[ANY],PTR[ANY]],

						[CHAR, CHAR],
					], token)
					assert case != -1 and case < 4, "???"
					if case == 0: self.stack.append((token, INT))
					if case == 1: self.stack.append((token, PTR[ANY]))
					if case == 2: self.stack.append((token, INT))
					if case == 3: self.stack.append((token, CHAR))
					self.last_case = case

				case Token(type=Operands.OP_MUL, value=val):
					self.check([INT, INT], token)
					self.stack.append((token, INT))

				case Token(type=Operands.OP_DIV, value=val):
					self.check([INT, INT], token)
					self.stack.append((token, INT))

				case Token(type=Operands.OP_MOD, value=val):
					self.check([INT, INT], token)
					self.stack.append((token, INT))

				case Token(type=Operands.OP_DIVMOD, value=val):
					self.check([INT, INT], token)
					self.stack.append((token, INT))
					self.stack.append((token, INT))

				case Token(type=Operands.OP_INCREMENT, value=val):
					case, stack_types = self.check_comb([
					 	[INT],
					 	[PTR[ANY]],
					 	[CHAR],
					], token)
					assert case != -1 and case < 3
					if case == 0: self.stack.append((token, INT))
					if case == 1: self.stack.append((token, PTR[ANY]))
					if case == 2: self.stack.append((token, CHAR))
					self.last_case = case

				case Token(type=Operands.OP_DECREMENT, value=val):
					case, stack_types = self.check_comb([
					 	[INT],
					 	[PTR[ANY]],
					 	[CHAR],
					], token)
					assert case != -1 and case < 3
					if case == 0: self.stack.append((token, INT))
					if case == 1: self.stack.append((token, PTR[ANY]))
					if case == 2: self.stack.append((token, CHAR))
					self.last_case = case

				case Token(type=Operands.OP_BLSH, value=val):
					self.check([INT, INT], token)
					self.stack.append((token, INT))

				case Token(type=Operands.OP_BRSH, value=val):
					self.check([INT, INT], token)
					self.stack.append((token, INT))

				case Token(type=Operands.OP_BAND, value=val):
					case, _ = self.check_comb([
						[INT,INT],
						[CHAR,CHAR],
						[BOOL,BOOL],
					], token)
					assert case != -1 and case < 3, "???"
					if case == 0: self.stack.append((token, INT))
					if case == 1: self.stack.append((token, BOOL))
					if case == 2: self.stack.append((token, CHAR))
					self.last_case = case

				case Token(type=Operands.OP_BOR, value=val):
					case, _ = self.check_comb([
						[INT,INT],
						[CHAR,CHAR],
						[BOOL,BOOL],
					], token)
					assert case != -1 and case < 3, "???"
					if case == 0: self.stack.append((token, INT))
					if case == 1: self.stack.append((token, BOOL))
					if case == 2: self.stack.append((token, CHAR))
					self.last_case = case

				case Token(type=Operands.OP_BXOR, value=val):
					case, _ = self.check_comb([
						[INT,INT],
						[CHAR,CHAR],
						[BOOL,BOOL],
					], token)
					assert case != -1 and case < 3, "???"
					if case == 0: self.stack.append((token, INT))
					if case == 1: self.stack.append((token, BOOL))
					if case == 2: self.stack.append((token, CHAR))
					self.last_case = case

				case Token(type=Operands.OP_EQ, value=val):
					t = self.check_same(2, token)
					self.stack.append((token, BOOL))

				case Token(type=Operands.OP_NE, value=val):
					t = self.check_same(2, token)
					self.stack.append((token, BOOL))

				case Token(type=Operands.OP_GT, value=val):
					t = self.check_same(2, token)
					self.stack.append((token, BOOL))

				case Token(type=Operands.OP_GE, value=val):
					t = self.check_same(2, token)
					self.stack.append((token, BOOL))

				case Token(type=Operands.OP_LT, value=val):
					t = self.check_same(2, token)
					self.stack.append((token, BOOL))

				case Token(type=Operands.OP_LE, value=val):
					t = self.check_same(2, token)
					self.stack.append((token, BOOL))

				case Token(type=OpTypes.OP_DUMP, value=val):
					self.check([ANY], token)

				case Token(type=OpTypes.OP_UDUMP, value=val):
					self.check([ANY], token)

				case Token(type=OpTypes.OP_CDUMP, value=val):
					self.check([ANY], token)

				case Token(type=OpTypes.OP_HEXDUMP, value=val):
					self.check([INT], token)

				case Token(type=OpTypes.OP_SYSCALL, value=val):
					self.check([INT], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_RSYSCALL1, value=val):
					self.check([ANY, INT], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_RSYSCALL2, value=val):
					self.check([ANY, ANY, INT], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_RSYSCALL3, value=val):
					self.check([ANY, ANY, ANY, INT], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_RSYSCALL4, value=val):
					self.check([ANY, ANY, ANY, ANY, INT], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_RSYSCALL5, value=val):
					self.check([ANY, ANY, ANY, ANY, ANY, INT], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_RSYSCALL6, value=val):
					self.check([ANY, ANY, ANY, ANY, ANY, ANY, INT], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_SYSCALL, value=val):
					self.check([INT], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_SYSCALL1, value=val):
					self.check([INT, ANY], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_SYSCALL2, value=val):
					self.check([INT, ANY, ANY], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_SYSCALL3, value=val):
					self.check([INT, ANY, ANY, ANY], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_SYSCALL4, value=val):
					self.check([INT, ANY, ANY, ANY, ANY], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_SYSCALL5, value=val):
					self.check([INT, ANY, ANY, ANY, ANY, ANY], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_SYSCALL6, value=val):
					self.check([INT, ANY, ANY, ANY, ANY, ANY, ANY], token)
					self.stack.append((token, INT))

				case Token(type=OpTypes.OP_EXIT, value=val):
					self.check([INT], token)

				case Token(type=FlowControl.OP_IF, value=val):
					self.block_stack.append(self.stack.copy())
					self.block_origin_stack.append(self.stack.copy())
					self.last_case = -1

				case Token(type=FlowControl.OP_ELIF, value=val):
					prev = self.block_stack.pop()
					flowinfo: FlowInfo = val

					assert flowinfo.prev, 'should have been caught as a parse error'
					if flowinfo.prev.type == FlowControl.OP_IF and not flowinfo.haselse:
						self.cmp_stack(self.stack, prev, IfException(val.prev.info, ''))
					if flowinfo.prev.type == FlowControl.OP_ELIF:
						self.cmp_stack(self.stack, prev, ElifException(val.prev.info, ''))

					self.block_stack.append(self.stack.copy())
					self.stack = self.block_origin_stack[-1].copy()
					self.last_case = -1

				case Token(type=FlowControl.OP_ELSE, value=val):
					prev = self.block_stack.pop()

					flowinfo: FlowInfo = val
					assert flowinfo.prev, 'should have been caught as a parse error'
					if flowinfo.prev.type == FlowControl.OP_ELIF:
						self.cmp_stack(self.stack, prev, ElseException(val.prev.info, ''))

					self.block_stack.append(self.stack.copy())
					self.stack = self.block_origin_stack[-1].copy()
					self.last_case = -1

				case Token(type=FlowControl.OP_WHILE, value=val):
					self.block_origin_stack.append(self.stack.copy())
					self.block_stack.append(self.stack.copy())
					self.last_case = -1

				case Token(type=FlowControl.OP_DO, value=val):
					if val.root.type in [FlowControl.OP_WITH, FlowControl.OP_LET]:
						continue
					self.check([BOOL], token)
					self.last_case = -1

					if val.root.type == FlowControl.OP_WHILE:
						prev = self.block_stack[-1]
						if len(prev) != len(self.stack):
							raise WhileException(self.stack[-1][0].info, "Overflow error. `while` until `do` needs to only push 1 bool")

				case Token(type=FlowControl.OP_END, value=val):
					self.last_case = -1
					if val.root.type in [FlowControl.OP_WITH, FlowControl.OP_LET]:
						self.locals.pop()
						continue
					prev = self.block_stack.pop()
					origin = self.block_origin_stack.pop()
					if val.root.type in [PreprocTypes.PROC]:
						procedure = val.root.value
						self.check([i[1] for i in procedure.out], token)
						if self.stack:
							if len(self.stack) == 1:
								a_token, a_type = self.stack.pop()
								raise ProcedureError(a_token.info, f"unhandled data on stack inside procedure ({a_type})", Reporting(val.root.info, ''))
							if len(self.stack) > 1:
								a_token, a_type = self.stack.pop()
								raise ProcedureError(a_token.info, f"unhandled data on stack inside procedure ({a_type}) ({len(self.stack)} more)", Reporting(val.root.info, ''))
						self.stack = prev
					elif val.root.type == FlowControl.OP_WHILE:
						self.cmp_stack(self.stack, prev, WhileException(token.info, ''))
						self.stack = prev
					elif val.root.type == FlowControl.OP_IF:
						self.cmp_stack(self.stack, prev, IfException(token.info, ''))
					elif val.root.type == FlowControl.OP_END:
						pass
					else:
						raise RuntimeError(NotImplemented, token)

				case Token(type=FlowControl.OP_LET, value=val):
					self.check([INT] * len(val.data), token)
					l = {}
					for tok in val.data:
						l[tok.value] = [tok, PTR[ANY]]
					self.locals.append(l)

				case Token(type=FlowControl.OP_WITH, value=val):
					self.check_length(len(val.data), token)
					l = {}
					for name in val.data:
						l[name.value] = self.stack.pop()
					self.locals.append(l)

				case Token(type=Intrinsics.OP_ARGC, value=val):
					self.stack.append((token, INT))

				case Token(type=Intrinsics.OP_ARGV, value=val):
					self.stack.append((token, PTR[ANY]))

				case Token(type=OpTypes.OP_STORE, value=val):
					self.check([PTR[ANY], CHAR], token)
				case Token(type=OpTypes.OP_STORE16, value=val):
					self.check([PTR[ANY], INT], token)
				case Token(type=OpTypes.OP_STORE32, value=val):
					self.check([PTR[ANY], INT], token)
				case Token(type=OpTypes.OP_STORE64, value=val):
					self.check([PTR[ANY], INT], token)

				case Token(type=OpTypes.OP_LOAD, value=val):
					t = self.check([PTR[ANY]], token)
					self.stack.append((token, derefType(t[0][1])))

				case Token(type=OpTypes.OP_LOAD16, value=val):
					t = self.check([PTR[ANY]], token)
					self.stack.append((token, derefType(t[0][1])))

				case Token(type=OpTypes.OP_LOAD32, value=val):
					t = self.check([PTR[ANY]], token)
					self.stack.append((token, derefType(t[0][1])))

				case Token(type=OpTypes.OP_LOAD64, value=val):
					t = self.check([PTR[ANY]], token)
					self.stack.append((token, derefType(t[0][1])))

				case Token(type=OpTypes.OP_WORD, value=key):
					for d in reversed(self.locals):
						if d.get(key, None) is not None:
							self.stack.append(d[key])
							break
					else:
						if key in self.procedures:
							self.check([i[1] for i in self.procedures[key].args], token)
							for i in self.procedures[key].out:
								self.stack.append(i)
						else:
							raise UnknownToken(token.info, "Unknown word")

				case Token(type=PreprocTypes.CAST, value=val):
					a = self.stack.pop()
					self.stack.append((a[0], val))

				case Token(type=OpTypes.OP_PUSHMEMORY, value=val):
					self.stack.append((token, PTR[ANY]))

				case Token(type=PreprocTypes.PROC, value=val):
					self.procedures[val.name] = val
					self.block_origin_stack.append(self.stack.copy())
					self.block_stack.append([])
					self.stack = []
					l = {}
					for tok, typ in val.args:
						l[tok.value] = [tok, typ]
					self.locals.append(l)
					self.last_case = -1


				case Token(type=PreprocTypes.CALL, value=val):
					self.check([i[1] for i in self.procedures[val].args], token)
					for i in self.procedures[val].out:
						self.stack.append(i)

				case _:
					raise RuntimeError(NotImplemented, token)
		if len(self.stack) == 1:
			a_token, a_type = self.stack.pop()
			raise StackNotEmpty(a_token.info, f"unhandled data on stack ({a_type})")
		if len(self.stack) > 1:
			a_token, a_type = self.stack.pop()
			raise StackNotEmpty(a_token.info, f"unhandled data on stack ({a_type}) ({len(self.stack)} more)")
		yield
