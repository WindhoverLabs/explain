function(explain_generate_symbol_map)
    set(TARGET_NAME ${ARGV0})
    # Define the function arguments.
    cmake_parse_arguments(PARSED_ARGS "" "INPUT_PATH;INPUT_FILE;DATABASE_NAME;OUTPUT_FILE" "" ${ARGN})
    
    add_custom_target(CDD_DB ALL
        COMMAND ${PROJECT_SOURCE_DIR}/tools/explain/python/generate_symbol_map 
        	${PARSED_ARGS_INPUT_PATH} 
        	${PARSED_ARGS_INPUT_FILE} 
        	${PARSED_ARGS_DATABASE_NAME} 
        	${PARSED_ARGS_OUTPUT_FILE} 
        	${PROJECT_BINARY_DIR}/host
    )
    add_dependencies(CDD_DB ${TARGET_NAME})
endfunction(explain_generate_symbol_map)
