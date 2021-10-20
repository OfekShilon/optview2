CC=clang++
CXX=clang++
RM=rm -f
MKDIR=mkdir
CPPFLAGS=-fsave-optimization-record -foptimization-record-file=./yaml_optimization_remarks/$(@:o=opt.yaml) -O3
LDFLAGS=
LDLIBS=

SRCS=$(wildcard *.cc)
OBJS=$(subst .cc,.o,$(SRCS))

all: another

another: $(OBJS)
	$(CXX) $(LDFLAGS) -o another $(OBJS) $(LDLIBS)

depend: .depend

.depend: $(SRCS)
	$(RM) ./.depend
	$(MKDIR) -p ./yaml_optimization_remarks
	$(CXX) $(CPPFLAGS) -MM $^ >> ./.depend;

clean:
	$(RM) $(OBJS) .depend *~ ./yaml_optimization_remarks/*

include .depend
