	.file	"launch.c"
	.text
	.section	.rodata.str1.1,"aMS",@progbits,1
.LC0:
	.string	"rp11-launch/1: launch-usage\n"
.LC1:
	.string	"rp11-launch/1: launch-invocation-id\n"
.LC2:
	.string	"rp11-launch/1: launch-stdio\n"
.LC3:
	.string	"rp11-launch/1: launch-descriptors\n"
.LC4:
	.string	"rp11-launch/1: launch-signals\n"
.LC5:
	.string	"/"
.LC6:
	.string	"rp11-launch/1: launch-chdir\n"
.LC7:
	.string	"/usr/bin/python3.14"
.LC8:
	.string	"-I"
.LC9:
	.string	"-S"
.LC10:
	.string	"/usr/local/libexec/freedom-blades-rp11/rp11_entry.py"
.LC11:
	.string	"run"
.LC12:
	.string	"--pass"
.LC13:
	.string	"A"
.LC14:
	.string	"LC_ALL=C"
.LC15:
	.string	"PATH=/usr/bin"
.LC16:
	.string	"rp11-launch/1: launch-exec-failed\n"
	.text
	.globl	rp11_main
	.type	rp11_main, @function
rp11_main:
	cmpq	$3, %rdi
	jne	.L2
	movq	8(%rsi), %rax
	cmpb	$45, (%rax)
	jne	.L2
	cmpb	$45, 1(%rax)
	jne	.L2
	cmpb	$112, 2(%rax)
	jne	.L2
	cmpb	$97, 3(%rax)
	jne	.L2
	cmpb	$115, 4(%rax)
	jne	.L2
	cmpb	$115, 5(%rax)
	jne	.L2
	cmpb	$0, 6(%rax)
	jne	.L2
	movq	16(%rsi), %rax
	cmpb	$65, (%rax)
	jne	.L2
	cmpb	$0, 1(%rax)
	je	.L19
.L2:
	movl	$1, %eax
	movl	$2, %edi
	movl	$.LC0, %esi
	movl	$28, %edx
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	movl	$231, %eax
	movl	$111, %edi
#APP
# 51 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	ud2
.L19:
	xorl	%ecx, %ecx
	xorl	%r8d, %r8d
.L3:
	movq	(%rdx), %rax
	testq	%rax, %rax
	je	.L32
	cmpb	$73, (%rax)
	jne	.L4
	cmpb	$78, 1(%rax)
	jne	.L4
	cmpb	$86, 2(%rax)
	jne	.L4
	cmpb	$79, 3(%rax)
	jne	.L4
	cmpb	$67, 4(%rax)
	jne	.L4
	cmpb	$65, 5(%rax)
	jne	.L4
	cmpb	$84, 6(%rax)
	jne	.L4
	cmpb	$73, 7(%rax)
	jne	.L4
	cmpb	$79, 8(%rax)
	jne	.L4
	cmpb	$78, 9(%rax)
	jne	.L4
	cmpb	$95, 10(%rax)
	jne	.L4
	cmpb	$73, 11(%rax)
	jne	.L4
	cmpb	$68, 12(%rax)
	jne	.L4
	movb	13(%rax), %sil
	cmpb	$61, %sil
	jne	.L5
	incq	%rcx
	leaq	14(%rax), %r8
	jmp	.L4
.L5:
	testb	%sil, %sil
	jne	.L4
	incq	%rcx
	xorl	%r8d, %r8d
.L4:
	addq	$8, %rdx
	jmp	.L3
.L32:
	decq	%rcx
	jne	.L7
	testq	%r8, %r8
	je	.L7
.L9:
	movb	(%r8,%rax), %dl
	leal	-48(%rdx), %ecx
	cmpb	$9, %cl
	jbe	.L20
	subl	$97, %edx
	cmpb	$5, %dl
	ja	.L7
.L20:
	incq	%rax
	cmpq	$32, %rax
	jne	.L9
	cmpb	$0, 32(%r8)
	je	.L10
.L7:
	movl	$1, %eax
	movl	$2, %edi
	movl	$.LC1, %esi
	movl	$36, %edx
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	movl	$231, %eax
	movl	$112, %edi
#APP
# 51 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	ud2
.L10:
	movl	$1, %r9d
	xorl	%edi, %edi
	movl	$72, %eax
	movq	%r9, %rsi
	movq	%rdi, %rdx
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	cmpq	$-4096, %rax
	jbe	.L11
	movl	$2, %edi
	movl	$.LC2, %esi
	movl	$28, %edx
	movq	%r9, %rax
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	movl	$231, %eax
	movl	$113, %edi
#APP
# 51 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	ud2
.L11:
	movl	$72, %eax
	movq	%r9, %rdi
	xorl	%edx, %edx
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	cmpq	$-4096, %rax
	jbe	.L12
	movl	$2, %edi
	movl	$.LC2, %esi
	movl	$28, %edx
	movq	%r9, %rax
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	movl	$231, %eax
	movl	$113, %edi
#APP
# 51 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	ud2
.L12:
	movl	$72, %eax
	movl	$2, %edi
	xorl	%edx, %edx
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	cmpq	$-4096, %rax
	jbe	.L13
	movl	$.LC2, %esi
	movl	$28, %edx
	movq	%r9, %rax
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	movl	$231, %eax
	movl	$113, %edi
#APP
# 51 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	ud2
.L13:
	movl	$436, %eax
	movl	$3, %edi
	movl	$4294967295, %esi
	xorl	%edx, %edx
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	testq	%rax, %rax
	je	.L14
	movl	$.LC3, %esi
	movl	$34, %edx
	movq	%r9, %rax
	movl	$2, %edi
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	movl	$231, %eax
	movl	$114, %edi
#APP
# 51 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	ud2
.L14:
	pushq	%rbx
	xorl	%esi, %esi
	movl	$1, %edi
	subq	$192, %rsp
	movq	%rsi, 48(%rsp)
	movq	%rsi, 56(%rsp)
	movq	%rsi, 64(%rsp)
	movq	%rsi, 72(%rsp)
	leaq	48(%rsp), %rsi
.L16:
	leal	-1(%rdi), %ecx
	movl	$262400, %edx
	shrq	%cl, %rdx
	andl	$1, %edx
	jne	.L15
	movl	$8, %r10d
	movl	$13, %eax
#APP
# 76 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	testq	%rax, %rax
	je	.L15
	movl	$1, %eax
	movl	$2, %edi
	movl	$.LC4, %esi
	movl	$30, %edx
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	movl	$231, %eax
	movl	$115, %edi
#APP
# 51 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	ud2
.L15:
	incq	%rdi
	cmpq	$65, %rdi
	jne	.L16
	xorl	%ecx, %ecx
	leaq	8(%rsp), %rsi
	movl	$8, %r10d
	xorl	%edx, %edx
	movq	%rcx, 8(%rsp)
	movl	$14, %eax
	movl	$2, %edi
#APP
# 76 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	testq	%rax, %rax
	je	.L17
	movl	$1, %eax
	movl	$.LC4, %esi
	movl	$30, %edx
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	movl	$231, %eax
	movl	$115, %edi
#APP
# 51 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	ud2
.L17:
	movl	$95, %eax
	movl	$63, %edi
#APP
# 51 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	movl	$80, %eax
	movl	$.LC5, %edi
#APP
# 51 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	testq	%rax, %rax
	je	.L18
	movl	$1, %eax
	movl	$.LC6, %esi
	movl	$28, %edx
	movl	$2, %edi
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	movl	$231, %eax
	movl	$116, %edi
#APP
# 51 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	ud2
.L18:
	movw	$15684, 92(%rsp)
	xorl	%edx, %edx
	leaq	128(%rsp), %rsi
	movabsq	$5283920020162104905, %rax
	movl	$1230982735, 88(%rsp)
	movl	$.LC7, %edi
	movq	%rax, 80(%rsp)
	movb	(%r8), %al
	movb	%al, 94(%rsp)
	movb	1(%r8), %al
	movb	%al, 95(%rsp)
	movb	2(%r8), %al
	movb	%al, 96(%rsp)
	movb	3(%r8), %al
	movb	%al, 97(%rsp)
	movb	4(%r8), %al
	movb	%al, 98(%rsp)
	movb	5(%r8), %al
	movb	%al, 99(%rsp)
	movb	6(%r8), %al
	movb	%al, 100(%rsp)
	movb	7(%r8), %al
	movb	%al, 101(%rsp)
	movb	8(%r8), %al
	movb	%al, 102(%rsp)
	movb	9(%r8), %al
	movb	%al, 103(%rsp)
	movb	10(%r8), %al
	movb	%al, 104(%rsp)
	movb	11(%r8), %al
	movb	%al, 105(%rsp)
	movb	12(%r8), %al
	movb	%al, 106(%rsp)
	movb	13(%r8), %al
	movb	%al, 107(%rsp)
	movb	14(%r8), %al
	movb	%al, 108(%rsp)
	movb	15(%r8), %al
	movb	%al, 109(%rsp)
	movb	16(%r8), %al
	movb	%al, 110(%rsp)
	movb	17(%r8), %al
	movb	%al, 111(%rsp)
	movb	18(%r8), %al
	movb	%al, 112(%rsp)
	movb	19(%r8), %al
	movb	%al, 113(%rsp)
	movb	20(%r8), %al
	movb	%al, 114(%rsp)
	movb	21(%r8), %al
	movb	%al, 115(%rsp)
	movb	22(%r8), %al
	movb	%al, 116(%rsp)
	movb	23(%r8), %al
	movb	%al, 117(%rsp)
	movb	24(%r8), %al
	movb	%al, 118(%rsp)
	movb	25(%r8), %al
	movb	%al, 119(%rsp)
	movb	26(%r8), %al
	movb	%al, 120(%rsp)
	movb	27(%r8), %al
	movb	%al, 121(%rsp)
	movb	28(%r8), %al
	movb	%al, 122(%rsp)
	movb	29(%r8), %al
	movb	%al, 123(%rsp)
	movb	30(%r8), %al
	movb	%al, 124(%rsp)
	movb	31(%r8), %al
	movq	%rdx, 40(%rsp)
	leaq	16(%rsp), %rdx
	movb	%al, 125(%rsp)
	xorl	%eax, %eax
	movq	%rax, 184(%rsp)
	leaq	80(%rsp), %rax
	movq	%rax, 32(%rsp)
	movl	$59, %eax
	movb	$0, 126(%rsp)
	movq	$.LC7, 128(%rsp)
	movq	$.LC8, 136(%rsp)
	movq	$.LC9, 144(%rsp)
	movq	$.LC10, 152(%rsp)
	movq	$.LC11, 160(%rsp)
	movq	$.LC12, 168(%rsp)
	movq	$.LC13, 176(%rsp)
	movq	$.LC14, 16(%rsp)
	movq	$.LC15, 24(%rsp)
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	movl	$1, %eax
	movl	$.LC16, %esi
	movl	$34, %edx
	movl	$2, %edi
#APP
# 63 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	movl	$231, %eax
	movl	$117, %edi
#APP
# 51 "launch.c" 1
	syscall
# 0 "" 2
#NO_APP
	ud2
	.size	rp11_main, .-rp11_main
	.section	.note.GNU-stack,"",@progbits
