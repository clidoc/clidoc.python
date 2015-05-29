#!/bin/bash
CLIDOC_PYTHON_SOURCE_DIR="$(dirname $0)/.."
CLIDOC_SOURCE_DIR="${CLIDOC_PYTHON_SOURCE_DIR}/../clidoc"
CLIDOC_BUILD_DIR="${CLIDOC_SOURCE_DIR}/build"
CLIDOC_MAIN_PATH="${CLIDOC_BUILD_DIR}/src/clidoc_main"

TARGET_DIR1="${CLIDOC_SOURCE_DIR}/resource/python"
TARGET_DIR2="${CLIDOC_BUILD_DIR}/resource/python"
CODEGEN_PY_PATH="${CLIDOC_PYTHON_SOURCE_DIR}/clidoc/codegen.py"

cp ${CODEGEN_PY_PATH} ${TARGET_DIR1}
cp ${CODEGEN_PY_PATH} ${TARGET_DIR2}

DOC_NAMES=(command default_value logic option_binding simple_option argument)
TEST_DOCS_PATH="${CLIDOC_SOURCE_DIR}/test/test_docs"
for doc_name in ${DOC_NAMES[@]}; do
	${CLIDOC_MAIN_PATH} -m python "${TEST_DOCS_PATH}/$doc_name" \
                      "${CLIDOC_PYTHON_SOURCE_DIR}/tests/clidoc_${doc_name}.py"
done
