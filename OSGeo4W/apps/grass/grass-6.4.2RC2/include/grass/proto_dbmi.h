#ifndef _PROTO_DBMI_H_
#define _PROTO_DBMI_H_

void db_Cstring_to_lowercase(char *s);
void db_Cstring_to_uppercase(char *s);
int db_add_column(dbDriver * driver, dbString * tableName, dbColumn * column);
void db__add_cursor_to_driver_state(dbCursor * cursor);
int db_alloc_cursor_column_flags(dbCursor * cursor);
int db_alloc_cursor_table(dbCursor * cursor, int ncols);
dbDirent *db_alloc_dirent_array(int count);
dbHandle *db_alloc_handle_array(int count);
dbIndex *db_alloc_index_array(int count);
int db_alloc_index_columns(dbIndex * index, int ncols);
dbString *db_alloc_string_array(int count);
dbTable *db_alloc_table(int ncols);
int db_append_string(dbString * x, const char *s);
void db_auto_print_errors(int flag);
void db_auto_print_protocol_errors(int flag);
int db_bind_update(dbCursor * cursor);
void *db_calloc(int n, int m);
int db_CatValArray_alloc(dbCatValArray * arr, int n);
int db_CatValArray_realloc(dbCatValArray * arr, int n);
void db_CatValArray_free(dbCatValArray * arr);
void db_CatValArray_init(dbCatValArray * arr);
void db_CatValArray_sort(dbCatValArray * arr);
int db_CatValArray_sort_by_value(dbCatValArray * arr);
int db_CatValArray_get_value(dbCatValArray * arr, int key, dbCatVal **);
int db_CatValArray_get_value_int(dbCatValArray * arr, int key, int *val);
int db_CatValArray_get_value_double(dbCatValArray * arr, int key,
				    double *val);
void db_char_to_lowercase(char *s);
void db_char_to_uppercase(char *s);
void db_clear_error(void);
void db__close_all_cursors(void);
int db_close_cursor(dbCursor * cursor);
int db_close_database(dbDriver * driver);
int db_close_database_shutdown_driver(dbDriver * driver);
int db_column_sqltype(dbDriver * driver, const char *tab, const char *col);
int db_column_Ctype(dbDriver * driver, const char *tab, const char *col);
int db_convert_Cstring_to_column_default_value(const char *Cstring,
					       dbColumn * column);
int db_convert_Cstring_to_column_value(const char *Cstring,
				       dbColumn * column);
int db_convert_Cstring_to_value(const char *Cstring, int sqltype,
				dbValue * value);
int db_convert_Cstring_to_value_datetime(const char *buf, int sqltype,
					 dbValue * value);
int db_convert_column_default_value_to_string(dbColumn * column,
					      dbString * string);
int db_convert_column_value_to_string(dbColumn * column, dbString * string);
int db_convert_value_datetime_into_string(dbValue * value, int sqltype,
					  dbString * string);
int db_convert_value_to_string(dbValue * value, int sqltype,
			       dbString * string);
void db_copy_dbmscap_entry(dbDbmscap * dst, dbDbmscap * src);
int db_copy_string(dbString * dst, dbString * src);
int db_table_to_sql(dbTable *, dbString *);
int db_copy_table(const char *, const char *, const char *, const char *,
		  const char *, const char *);
int db_copy_table_where(const char *, const char *, const char *,
			const char *, const char *, const char *,
			const char *);
int db_copy_table_select(const char *, const char *, const char *,
			 const char *, const char *, const char *,
			 const char *);
int db_copy_table_by_ints(const char *, const char *, const char *,
			  const char *, const char *, const char *,
			  const char *, int *, int);
void db_copy_value(dbValue * dst, dbValue * src);
int db_create_database(dbDriver * driver, dbHandle * handle);
int db_create_index(dbDriver * driver, dbIndex * index);
int db_create_index2(dbDriver * driver, const char *table_name,
		     const char *column_name);
int db_create_table(dbDriver * driver, dbTable * table);
int db_d_add_column(void);
int db_d_bind_update(void);
const char *db_dbmscap_filename(void);
int db_d_close_cursor(void);
int db_d_close_database(void);
int db_d_create_database(void);
int db_d_create_index(void);
int db_d_create_table(void);
int db_d_delete(void);
int db_d_delete_database(void);
int db_d_describe_table(void);
int db_d_drop_column(void);
int db_d_drop_index(void);
int db_d_drop_table(void);
void db_debug(const char *s);
void db_debug_off(void);
void db_debug_on(void);
int db_delete(dbCursor * cursor);
int db_delete_database(dbDriver * driver, dbHandle * handle);
int db_delete_table(const char *, const char *, const char *);
int db_describe_table(dbDriver * driver, dbString * name, dbTable ** table);
int db_d_execute_immediate(void);
int db_d_begin_transaction(void);
int db_d_commit_transaction(void);
int db_d_fetch(void);
int db_d_find_database(void);
int db_d_get_num_rows(void);
int db_d_grant_on_table(void);
int db_d_insert(void);
dbDirent *db_dirent(const char *dirname, int *n);
int db_d_list_databases(void);
int db_d_list_indexes(void);
int db_d_list_tables(void);
int db_d_open_database(void);
int db_d_open_insert_cursor(void);
int db_d_open_select_cursor(void);
int db_d_open_update_cursor(void);
void db_double_quote_string(dbString * src);
int db_driver(int argc, char *argv[]);

int db_driver_mkdir(const char *path, int mode, int parentdirs);
int db_drop_column(dbDriver * driver, dbString * tableName,
		   dbString * columnName);
void db__drop_cursor_from_driver_state(dbCursor * cursor);
int db_drop_index(dbDriver * driver, dbString * name);
int db_drop_table(dbDriver * driver, dbString * name);
void db_drop_token(dbToken token);
int db_d_update(void);
int db_d_version(void);
int db_enlarge_string(dbString * x, int len);
void db_error(const char *s);
int db_execute_immediate(dbDriver * driver, dbString * SQLstatement);
int db_begin_transaction(dbDriver * driver);
int db_commit_transaction(dbDriver * driver);
int db_fetch(dbCursor * cursor, int position, int *more);
int db_find_database(dbDriver * driver, dbHandle * handle, int *found);
dbAddress db_find_token(dbToken token);
void *db_free(void *s);
void db_free_column(dbColumn * column);
void db_free_cursor(dbCursor * cursor);
void db_free_cursor_column_flags(dbCursor * cursor);
void db_free_dbmscap(dbDbmscap * list);
void db_free_dirent_array(dbDirent * dirent, int count);
void db_free_handle(dbHandle * handle);
void db_free_handle_array(dbHandle * handle, int count);
void db_free_index(dbIndex * index);
void db_free_index_array(dbIndex * list, int count);
void db_free_string(dbString * x);
void db_free_string_array(dbString * a, int n);
void db_free_table(dbTable * table);
int db_get_column(dbDriver * Driver, const char *tname, const char *cname,
		  dbColumn ** Column);
dbValue *db_get_column_default_value(dbColumn * column);
const char *db_get_column_description(dbColumn * column);
int db_get_column_host_type(dbColumn * column);
int db_get_column_length(dbColumn * column);
const char *db_get_column_name(dbColumn * column);
int db_get_column_precision(dbColumn * column);
int db_get_column_scale(dbColumn * column);
int db_get_column_select_priv(dbColumn * column);
int db_get_column_sqltype(dbColumn * column);
int db_get_column_update_priv(dbColumn * column);
dbValue *db_get_column_value(dbColumn * column);
int db_get_connection(dbConnection * connection);
int db_get_cursor_number_of_columns(dbCursor * cursor);
dbTable *db_get_cursor_table(dbCursor * cursor);
dbToken db_get_cursor_token(dbCursor * cursor);
const char *db_get_default_driver_name(void);
const char *db_get_default_database_name(void);
const char *db_get_default_schema_name(void);
const char *db_get_default_group_name(void);
dbDriverState *db__get_driver_state(void);
int db_get_error_code(void);
const char *db_get_error_msg(void);
const char *db_get_error_who(void);
const char *db_get_handle_dbname(dbHandle * handle);
const char *db_get_handle_dbschema(dbHandle * handle);
const char *db_get_index_column_name(dbIndex * index, int column_num);
const char *db_get_index_name(dbIndex * index);
int db_get_index_number_of_columns(dbIndex * index);
const char *db_get_index_table_name(dbIndex * index);
int db_get_num_rows(dbCursor * cursor);
char *db_get_string(dbString * x);
dbColumn *db_get_table_column(dbTable * table, int n);
int db_get_table_delete_priv(dbTable * table);
const char *db_get_table_description(dbTable * table);
int db_get_table_insert_priv(dbTable * table);
const char *db_get_table_name(dbTable * table);
int db_get_table_number_of_columns(dbTable * table);
int db_get_table_number_of_rows(dbDriver * driver, dbString * sql);
int db_get_table_select_priv(dbTable * table);
int db_get_table_update_priv(dbTable * table);
double db_get_value_as_double(dbValue * value, int ctype);
int db_get_value_day(dbValue * value);
double db_get_value_double(dbValue * value);
int db_get_value_hour(dbValue * value);
int db_get_value_int(dbValue * value);
int db_get_value_minute(dbValue * value);
int db_get_value_month(dbValue * value);
double db_get_value_seconds(dbValue * value);
const char *db_get_value_string(dbValue * value);
int db_get_value_year(dbValue * value);
int db_grant_on_table(dbDriver * driver, const char *tableName, int priv,
		      int to);
int db_has_dbms(void);
void db_init_column(dbColumn * column);
void db_init_cursor(dbCursor * cursor);
void db__init_driver_state(void);
void db_init_handle(dbHandle * handle);
void db_init_index(dbIndex * index);
void db_init_string(dbString * x);
void db_init_table(dbTable * table);
int db_insert(dbCursor * cursor);
void db_interval_range(int sqltype, int *from, int *to);
int db_isdir(const char *path);
int db_legal_tablename(const char *s);
int db_list_databases(dbDriver * driver, dbString * path, int npaths,
		      dbHandle ** handles, int *count);
const char *db_list_drivers(void);
int db_list_indexes(dbDriver * driver, dbString * table_name, dbIndex ** list,
		    int *count);
int db_list_tables(dbDriver * driver, dbString ** names, int *count,
		   int system);
void *db_malloc(int n);
void db__mark_database_closed(void);
void db__mark_database_open(const char *dbname, const char *dbpath);
void db_memory_error(void);
dbToken db_new_token(dbAddress address);
int db_nocase_compare(const char *a, const char *b);
void db_noproc_error(int procnum);
int db_open_database(dbDriver * driver, dbHandle * handle);
int db_open_insert_cursor(dbDriver * driver, dbCursor * cursor);
int db_open_select_cursor(dbDriver * driver, dbString * select,
			  dbCursor * cursor, int mode);
int db_open_update_cursor(dbDriver * driver, dbString * table_name,
			  dbString * select, dbCursor * cursor, int mode);
void db_print_column_definition(FILE * fd, dbColumn * column);
void db_print_error(void);
void db_print_index(FILE * fd, dbIndex * index);
void db_print_table_definition(FILE * fd, dbTable * table);
void db_procedure_not_implemented(const char *name);
void db_protocol_error(void);
dbDbmscap *db_read_dbmscap(void);
void *db_realloc(void *s, int n);
int db__recv_char(char *d);
int db__recv_column_default_value(dbColumn * column);
int db__recv_column_definition(dbColumn * column);
int db__recv_column_value(dbColumn * column);
int db__recv_datetime(dbDateTime * t);
int db__recv_double(double *d);
int db__recv_double_array(double **x, int *n);
int db__recv_float(float *d);
int db__recv_float_array(float **x, int *n);
int db__recv_handle(dbHandle * handle);
int db__recv_index(dbIndex * index);
int db__recv_index_array(dbIndex ** list, int *count);
int db__recv_int(int *n);
int db__recv_int_array(int **x, int *n);
int db__recv_procnum(int *n);
int db__recv_return_code(int *ret_code);
int db__recv_short(short *n);
int db__recv_short_array(short **x, int *n);
int db__recv_string(dbString * x);
int db__recv_string_array(dbString ** a, int *n);
int db__recv_table_data(dbTable * table);
int db__recv_table_definition(dbTable ** table);
int db__recv_token(dbToken * token);
int db__recv_value(dbValue * value, int Ctype);
int db__send_Cstring(const char *s);
int db__send_char(int d);
int db__send_column_default_value(dbColumn * column);
int db__send_column_definition(dbColumn * column);
int db__send_column_value(dbColumn * column);
int db__send_datetime(dbDateTime * t);
int db__send_double(double d);
int db__send_double_array(const double *x, int n);
int db__send_failure(void);
int db__send_float(float d);
int db__send_float_array(const float *x, int n);
int db__send_handle(dbHandle * handle);
int db__send_index(dbIndex * index);
int db__send_index_array(dbIndex * list, int count);
int db__send_int(int n);
int db__send_int_array(const int *x, int n);
int db__send_procedure_not_implemented(int n);
int db__send_procedure_ok(int n);
int db__send_short(int n);
int db__send_short_array(const short *x, int n);
int db__send_string(dbString * x);
int db__send_string_array(dbString * a, int count);
int db__send_success(void);
int db__send_table_data(dbTable * table);
int db__send_table_definition(dbTable * table);
int db__send_token(dbToken * token);
int db__send_value(dbValue * value, int Ctype);
int db_select_CatValArray(dbDriver * driver, const char *tab, const char *key,
			  const char *col, const char *where,
			  dbCatValArray * Cvarr);
int db_select_int(dbDriver * driver, const char *table, const char *column,
		  const char *where, int **pval);
int db_select_value(dbDriver * driver, const char *table, const char *key,
		    int id, const char *column, dbValue * value);
int db_set_column_description(dbColumn * column, const char *description);
void db_set_column_has_defined_default_value(dbColumn * column);
void db_set_column_has_undefined_default_value(dbColumn * column);
void db_set_column_host_type(dbColumn * column, int type);
void db_set_column_length(dbColumn * column, int length);
int db_set_column_name(dbColumn * column, const char *name);
void db_set_column_null_allowed(dbColumn * column);
void db_set_column_precision(dbColumn * column, int precision);
void db_set_column_scale(dbColumn * column, int scale);
void db_set_column_select_priv_granted(dbColumn * column);
void db_set_column_select_priv_not_granted(dbColumn * column);
void db_set_column_sqltype(dbColumn * column, int sqltype);
void db_set_column_update_priv_granted(dbColumn * column);
void db_set_column_update_priv_not_granted(dbColumn * column);
void db_set_column_use_default_value(dbColumn * column);
int db_set_connection(dbConnection * connection);
void db_set_cursor_column_flag(dbCursor * cursor, int col);
void db_set_cursor_column_for_update(dbCursor * cursor, int col);
void db_set_cursor_mode(dbCursor * cursor, int mode);
void db_set_cursor_mode_insensitive(dbCursor * cursor);
void db_set_cursor_mode_scroll(dbCursor * cursor);
void db_set_cursor_table(dbCursor * cursor, dbTable * table);
void db_set_cursor_token(dbCursor * cursor, dbToken token);
void db_set_cursor_type_insert(dbCursor * cursor);
void db_set_cursor_type_readonly(dbCursor * cursor);
void db_set_cursor_type_update(dbCursor * cursor);
int db_set_default_connection(void);
void db_set_error_who(const char *me);
int db_set_handle(dbHandle * handle, const char *dbName, const char *dbPath);
int db_set_index_column_name(dbIndex * index, int column_num,
			     const char *name);
int db_set_index_name(dbIndex * index, const char *name);
int db_set_index_table_name(dbIndex * index, const char *name);
int db_set_index_type_non_unique(dbIndex * index);
int db_set_index_type_unique(dbIndex * index);
void db__set_protocol_fds(FILE * send, FILE * recv);
int db_set_string(dbString * x, const char *s);
int db_set_string_no_copy(dbString * x, char *s);
void db_set_table_delete_priv_granted(dbTable * table);
void db_set_table_delete_priv_not_granted(dbTable * table);
int db_set_table_description(dbTable * table, const char *description);
void db_set_table_insert_priv_granted(dbTable * table);
void db_set_table_insert_priv_not_granted(dbTable * table);
int db_set_table_name(dbTable * table, const char *name);
void db_set_table_select_priv_granted(dbTable * table);
void db_set_table_select_priv_not_granted(dbTable * table);
void db_set_table_update_priv_granted(dbTable * table);
void db_set_table_update_priv_not_granted(dbTable * table);
void db_set_value_datetime_current(dbValue * value);
void db_set_value_datetime_not_current(dbValue * value);
void db_set_value_day(dbValue * value, int day);
void db_set_value_double(dbValue * value, double d);
void db_set_value_hour(dbValue * value, int hour);
void db_set_value_int(dbValue * value, int i);
void db_set_value_minute(dbValue * value, int minute);
void db_set_value_month(dbValue * value, int month);
void db_set_value_not_null(dbValue * value);
void db_set_value_null(dbValue * value);
void db_set_value_seconds(dbValue * value, double seconds);
int db_set_value_string(dbValue * value, const char *s);
void db_set_value_year(dbValue * value, int year);
int db_shutdown_driver(dbDriver * driver);
const char *db_sqltype_name(int sqltype);
int db_sqltype_to_Ctype(int sqltype);
dbDriver *db_start_driver(const char *name);
dbDriver *db_start_driver_open_database(const char *drvname,
					const char *dbname);
int db__start_procedure_call(int procnum);
char *db_store(const char *s);
void db_strip(char *buf);
void db_syserror(const char *s);
int db_table_exists(const char *drvname, const char *dbname,
		    const char *tabname);
int db_test_column_has_default_value(dbColumn * column);
int db_test_column_has_defined_default_value(dbColumn * column);
int db_test_column_has_undefined_default_value(dbColumn * column);
int db_test_column_null_allowed(dbColumn * column);
int db_test_column_use_default_value(dbColumn * column);
int db_test_cursor_any_column_flag(dbCursor * cursor);
int db_test_cursor_any_column_for_update(dbCursor * cursor);
int db_test_cursor_column_flag(dbCursor * cursor, int col);
int db_test_cursor_column_for_update(dbCursor * cursor, int col);
int db_test_cursor_mode_insensitive(dbCursor * cursor);
int db_test_cursor_mode_scroll(dbCursor * cursor);
int db_test_cursor_type_fetch(dbCursor * cursor);
int db_test_cursor_type_insert(dbCursor * cursor);
int db_test_cursor_type_update(dbCursor * cursor);
int db__test_database_open(void);
int db_test_index_type_unique(dbIndex * index);
int db_test_value_datetime_current(dbValue * value);
int db_test_value_isnull(dbValue * value);
void db_unset_column_has_default_value(dbColumn * column);
void db_unset_column_null_allowed(dbColumn * column);
void db_unset_column_use_default_value(dbColumn * column);
void db_unset_cursor_column_flag(dbCursor * cursor, int col);
void db_unset_cursor_column_for_update(dbCursor * cursor, int col);
void db_unset_cursor_mode(dbCursor * cursor);
void db_unset_cursor_mode_insensitive(dbCursor * cursor);
void db_unset_cursor_mode_scroll(dbCursor * cursor);
int db_update(dbCursor * cursor);
int db_gversion(dbDriver * driver, dbString * client_version,
		dbString * driver_version);
const char *db_whoami(void);
void db_zero(void *s, int n);
void db_zero_string(dbString * x);
unsigned int db_sizeof_string(dbString * x);
int db_set_login(const char *, const char *, const char *, const char *);
int db_get_login(const char *, const char *, const char **, const char **);

#endif
