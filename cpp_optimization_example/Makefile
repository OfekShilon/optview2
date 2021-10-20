CC=clang++
CXX=clang++
RM=rm -f
MKDIR_P=mkdir -p
OBJS_DIR=objs
DEPENDS_FILE=${OBJS_DIR}/.depend
YAML_OUTPUT_DIR=yaml_optimization_remarks
CPPFLAGS=-O3
LDFLAGS=
LDLIBS=
BINARY_NAME=example

SRCS=$(wildcard *.cc)
OBJS=$(addprefix $(OBJS_DIR)/,$(subst .cc,.o,$(SRCS)))

.PHONY: output_folder

all: output_folder ${BINARY_NAME}

directories: ${YAML_OUTPUT_DIR} ${OBJS_DIR}

${YAML_OUTPUT_DIR} ${OBJS_DIR}:
	${MKDIR_P} $@

${BINARY_NAME}: $(OBJS)
	$(CXX) $(LDFLAGS) -o $(BINARY_NAME) $(OBJS) $(LDLIBS)

${OBJS_DIR}/%.o : %.cc
	$(CXX) -c $(CFLAGS) $(CPPFLAGS) -fsave-optimization-record -foptimization-record-file=./${YAML_OUTPUT_DIR}/$(patsubst %.o,%.opt.yaml,$(notdir $@)) $< -o $@

depend: $(DEPENDS_FILE)

$(DEPENDS_FILE): $(SRCS)
	$(RM) $(DEPENDS_FILE)
	$(MKDIR_P) ${YAML_OUTPUT_DIR} ${OBJS_DIR}
	$(CXX) $(CPPFLAGS) -MM $^ >> $(DEPENDS_FILE)

clean:
	$(RM) -r ${YAML_OUTPUT_DIR} ${OBJS_DIR}

include $(DEPENDS_FILE)
