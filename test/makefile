##############################################################################
## File:
##   $Id: makefile 1.1 2016/06/14 16:47:23EDT czogby Exp  $
##
## Purpose:
##   Makefile for building the UT-Assert example unit tests
##
##   $Log: makefile  $
##   Revision 1.1 2016/06/14 16:47:23EDT czogby 
##   Initial revision
##   Member added to project /FSW-TOOLs-REPOSITORY/ut-assert/example/fsw/unit_test/project.pj
##
##############################################################################
## GNU Makefile for building UT unit tests

#
# Supported MAKEFILE targets:
#   clean - deletes object files, executables, output files, and gcov files
#   all   - makes example_testrunner.exe
#   run   - runs example_testrunner.exe
#   gcov  - prints a GCOV coverage report (make all, make run, make gcov)
#
# GCOV is disabled by default.  If you are using the source level debugger you will want to 
# disable GCOV.  To enable GCOV you can override the ENABLE_GCOV variable on the command line 
# by setting it to TRUE.  For example "make ENABLE_GCOV=TRUE".
#

#
# VPATH specifies the search paths for source files outside of the current directory.  Note that
# all object files will be created in the current directory even if the source file is not in the 
# current directory.
#
VPATH := .
# ut_assert src directory
VPATH += ../../ut_assert/src
# Application under test directory
VPATH += ../src

EXPLAIN_PATH=../

#
# INCLUDES specifies the search paths for include files outside of the current directory.  
# Note that the -I is required. 
#
INCLUDES := -I.
INCLUDES += -I../../ut_assert/inc
INCLUDES += -I$(EXPLAIN_PATH)/src
INCLUDES += -I$(EXPLAIN_PATH)/include


#
# FLIGHT_OBJS specifies flight software object files.
#
FLIGHT_OBJS := ccsds.o utils.o cfe_sb_util.o explain.o list.o memtools.o message.o parser.o usage.o

#
# UT_OBJS specifies unit test object files.
#
UT_OBJS += utassert.o
UT_OBJS += utlist.o
UT_OBJS += uttest.o
UT_OBJS += uttools.o
UT_OBJS += explain_app_test.o
UT_OBJS += explain_testrunner.o
UT_OBJS += explain_test_utils.o

#
# UT_TEST_RUNNER specifies the name of the test runner.
#
UT_TEST_RUNNER = explain_testrunner.exe

###############################################################################

COMPILER=gcc
LINKER=gcc

#
# Compiler and Linker Options
#
GCOV_COPT = -fprofile-arcs -ftest-coverage -pg -p
GCOV_LOPT = -pg -p -fprofile-arcs -ftest-coverage -lgcov -lm
JSON_LOPT = -ljson

#WARNINGS = -Wall -W -ansi -Werror -Wstrict-prototypes -Wundef
WARNINGS = -Wall -Wstrict-prototypes -Wundef
DEBUGGER = -g

COPT = $(WARNINGS) $(DEBUGGER) $(GCOV_COPT) -DUT_VERBOSE -Wno-deprecated-declarations

LOPT = $(GCOV_LOPT) 

###############################################################################
## Rule to make the specified TARGET
##
%.exe: %.o
	$(LINKER) $(LOPT) $^ -o $*.exe $(JSON_LOPT)

###############################################################################
##  "C" COMPILER RULE
##
%.o: %.c
	$(COMPILER) -c $(COPT) $(INCLUDES) $< 

##############################################################################
##

all:$(UT_TEST_RUNNER)

$(UT_TEST_RUNNER): $(UT_OBJS) $(FLIGHT_OBJS)

clean ::
	rm -f *.o *.exe *.gcda *.gcno *.gcov gmon.out

run ::
	./$(UT_TEST_RUNNER)

gcov ::
	@echo
	@gcov $(FLIGHT_OBJS:.o=.gcda) | sed 'N;s/\n/ /' | \
		sed -n '/File/p' | sed '/ads/d' | sed -e '/\.h/d'  | \
		sed 's/ Lines executed:/ /; s/File/gcov:/; s/of// '
	@rm -f *.gcda *.gcno
	@echo

# end of file
