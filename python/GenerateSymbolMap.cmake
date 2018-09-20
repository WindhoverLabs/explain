function(explain_generate_symbol_map)
    set(TARGET_NAME ${ARGV0})
    # Define the function arguments.
    cmake_parse_arguments(PARSED_ARGS "" "INPUT_PATH;INPUT_FILE;DATABASE_NAME;OUTPUT_FILE" "" ${ARGN})
    
    add_custom_target(${TARGET_NAME}_DB
        DEPENDS EXPLAIN_INSTALL pyliner_scripting_engine
        COMMAND ${PROJECT_SOURCE_DIR}/tools/explain/python/generate_symbol_map 
        	${PARSED_ARGS_INPUT_PATH} 
        	${PARSED_ARGS_INPUT_FILE} 
        	${PARSED_ARGS_DATABASE_NAME} 
        	${PARSED_ARGS_OUTPUT_FILE} 
        	${PROJECT_BINARY_DIR}/host
    )
    add_dependencies(${TARGET_NAME}_DB ${TARGET_NAME})
    add_dependencies(pyliner_scripting_engine ${TARGET_NAME}_DB)
endfunction(explain_generate_symbol_map)

function(explain_read_elf)
    set(TARGET_NAME ${ARGV0})
    # Define the function arguments.
    cmake_parse_arguments(PARSED_ARGS "" "INPUT_PATH;DATABASE_NAME" "" ${ARGN})
    
    add_custom_target(${TARGET_NAME}_DB
        DEPENDS EXPLAIN_INSTALL
        COMMAND ${PROJECT_SOURCE_DIR}/tools/explain/python/read_elf 
        	${PARSED_ARGS_DATABASE_NAME} 
        	${PARSED_ARGS_INPUT_PATH}
        	${PROJECT_BINARY_DIR}/host
    )
    add_dependencies(${TARGET_NAME}_DB ${TARGET_NAME})
    add_dependencies(pyliner_scripting_engine ${TARGET_NAME}_DB)
    add_dependencies(explain_parsing ${TARGET_NAME}_DB)
    
endfunction(explain_read_elf)

function(explain_generate_cookie)
    # Define the function arguments.
    cmake_parse_arguments(PARSED_ARGS "" "DATABASE_NAME;OUTPUT_FILE" "" ${ARGN})
    
    add_custom_target(cookie
        DEPENDS EXPLAIN_INSTALL explain_parsing
        COMMAND ${PROJECT_SOURCE_DIR}/tools/explain/python/generate_cookie
        	${PARSED_ARGS_DATABASE_NAME} 
        	${PARSED_ARGS_OUTPUT_FILE} 
        	${PROJECT_BINARY_DIR}/host
    )
    add_dependencies(pyliner_scripting_engine cookie)
endfunction(explain_generate_cookie)

function(explain_setup)
    add_custom_target(EXPLAIN_INSTALL
        COMMAND ${PROJECT_SOURCE_DIR}/tools/explain/python/setup_explain 
        	${PROJECT_BINARY_DIR}/host
    )
    add_dependencies(pyliner_scripting_engine EXPLAIN_INSTALL)
endfunction(explain_setup)
