IDIR=../include
LIB=-Wl,-Bstatic -ljson -Wl,-Bdynamic
CC=gcc
CFLAGS=-g -Wno-deprecated-declarations -fPIC -I$(IDIR)
STATICLIB=$(shell find /usr/lib/ -type f -name "libjson-c.a") 

ODIR=obj

_DEPS = cfe_sb.h utils.h cfe_mission_cfg.h common_types.h ccsds.h memtools.h list.h message.h usage.h explain.h parser.h 
DEPS = $(patsubst %,$(IDIR)/%,$(_DEPS))

_OBJ = cfe_sb_util.o utils.o ccsds.o memtools.o list.o message.o usage.o explain.o parser.o example.o
OBJ = $(patsubst %,$(ODIR)/%,$(_OBJ))

_OBJ_LIB = cfe_sb_util.o utils.o ccsds.o memtools.o list.o message.o usage.o explain.o parser.o
OBJ_LIB = $(patsubst %,$(ODIR)/%,$(_OBJ_LIB))

$(ODIR)/%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS) 

all: example.exe libexplain.so archive

example.exe: $(OBJ)
	$(CC) -o $@ $^ $(LIB) 

libexplain.so: $(OBJ_LIB)
	$(CC) -shared -o $@ $^

archive: $(OBJ_LIB)
	cd obj; \
	ar x $(STATICLIB)
	ar rcs libexplain.a obj/*.o


.PHONY: clean

clean:
	rm -f *.exe *.so *.a $(ODIR)/*.o *~ core $(INCDIR)/*~
