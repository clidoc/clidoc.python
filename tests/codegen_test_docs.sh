CLIDOC_MAIN=../../clidoc/build/src/clidoc_main
TEST_DOCS_PATH=../../clidoc/test/test_docs
DOC_NAMES=(command default_value logic option_binding simple_option)
for doc_name in ${DOC_NAMES[@]}; do
	${CLIDOC_MAIN} -m python "${TEST_DOCS_PATH}/$doc_name" clidoc_${doc_name}.py
done
