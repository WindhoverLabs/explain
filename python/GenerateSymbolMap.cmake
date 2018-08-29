function(explain_generate_symbol_map)
    set(TARGET_NAME ${ARGV0})
    # Define the function arguments.
    cmake_parse_arguments(PARSED_ARGS "" "INPUT_PATH;INPUT_FILE;DATABASE_NAME;OUTPUT_FILE" "" ${ARGN})
    
    add_custom_target(${TARGET_NAME}_DB ALL
        DEPENDS EXPLAIN_INSTALL
        COMMAND ${PROJECT_SOURCE_DIR}/tools/explain/python/generate_symbol_map 
        	${PARSED_ARGS_INPUT_PATH} 
        	${PARSED_ARGS_INPUT_FILE} 
        	${PARSED_ARGS_DATABASE_NAME} 
        	${PARSED_ARGS_OUTPUT_FILE} 
        	${PROJECT_BINARY_DIR}/host
    )
    add_dependencies(${TARGET_NAME}_DB ${TARGET_NAME})
endfunction(explain_generate_symbol_map)


function(explain_setup)
    set(TARGET_NAME ${ARGV0})
    
    add_custom_target(EXPLAIN_INSTALL ALL
        COMMAND ${PROJECT_SOURCE_DIR}/tools/explain/python/setup_explain 
        	${PROJECT_BINARY_DIR}/host
    )
endfunction(explain_setup)