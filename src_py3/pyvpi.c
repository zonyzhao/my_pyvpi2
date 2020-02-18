#include "pyvpi.h"

/*****************************************************************************
 * This is all code for python.
 *****************************************************************************/
int  print_level     = PRINT_NOTE;

PyObject *VpiError;
PyObject *PyError;

PyObject *DumbTuple;
PyObject *DumbDict;


/*****************************************************************************
 * pyvpi_CheckError()
 * Checks if an error was reported by the last vpi function called
 * and, if so, set VpiError and return error code.
 *****************************************************************************/
int 
pyvpi_CheckError(void)
{
    int              error_code;
    s_vpi_error_info error_info;

    error_code = vpi_chk_error( &error_info );
    if ( error_code && error_info.message ) {
        PyErr_SetString(VpiError,  error_info.message);
    }
    return error_code;
}

static int 
CheckError(void)
{
    int              error_code;
    s_vpi_error_info error_info;

    error_code = vpi_chk_error( &error_info );
    if ( error_code && error_info.message ) {
        vpi_printf("%s\n",error_info.message);
    }
    return error_code;
}

static PyObject* 
pyvpi_Print(PyObject *self, PyObject *args)
{
    PLI_BYTE8 *str;
    if (!PyArg_ParseTuple(args, "s", &str))
    {
        PyErr_SetString(VpiError,  "Error args, must be (str).");
        return NULL;
    }
    vpi_printf("%s",str);
    Py_XINCREF(Py_None);
    return Py_None;
}

static PyObject* 
pyvpi_callwithsvscopebyname(PyObject *self, PyObject *args)
{
    PLI_BYTE8 *str;
    PyObject *func;
    PyObject *pargs;
    if (!PyArg_ParseTuple(args, "sO|O",&str, &func, &pargs))
    {
        PyErr_SetString(VpiError,  "Error args, must be {func, str, args}");
        return NULL;
    }
    svScope scope = svGetScopeFromName(str);
    vpi_printf("set scope to %s\n",str);
    vpi_printf("set function to %s\n",Py_TYPE(func)->tp_name);
    vpi_printf("set pargs to %d\n", pargs);
    svSetScope(scope);
    return PyObject_CallObject(func, pargs);
}

static PyObject* 
pyvpi_setsvscopebyname(PyObject *self, PyObject *args)
{
    PLI_BYTE8 *str;
    if (!PyArg_ParseTuple(args, "s", &str))
    {
        PyErr_SetString(VpiError,  "Error args, must be (str).");
        return NULL;
    }
    svScope scope = svGetScopeFromName(str);
   // vpi_printf("%s",str);
    svSetScope(scope);
    Py_XINCREF(Py_None);
    return Py_None;
}

static PyObject* 
pyvpi_getSvScopeName(void)
{
    PLI_BYTE8 *str;
    svScope scope = svGetScope();
    if(scope == NULL)
    {
        str = "";
    }
    else{
        str = svGetNameFromScope(scope);
    }
    return Py_BuildValue("s", str);
}

/* for obtaining handles */
/*****************************************************************************
 * pyvpi_HandleByName()
 * XXTERN vpiHandle  vpi_handle_by_name  PROTO_PARAMS((PLI_BYTE8 *name,
 *                                                     vpiHandle scope));
 *****************************************************************************/
static PyObject* 
pyvpi_HandleByName(PyObject *self, PyObject *args)
{
    PLI_BYTE8 *name;
    p_pyvpi_handle scope = (p_pyvpi_handle)Py_None,oans;
    vpiHandle ans;
    if (!PyArg_ParseTuple(args, "s|O", &name,&scope))
    {
        PyErr_SetString(VpiError,  "Error args, must be (str,pyvpi.Handle).");
        return NULL;
    }

    if (!PyObject_TypeCheck(scope,&pyvpi_handle_Type)) {
        pyvpi_debug("handleByName 's 2nd arg is "
                    "not pyvpi.Handle type, trade scope as NULL.\n");
        ans = vpi_handle_by_name(name, NULL);
    }
    else {
        ans = vpi_handle_by_name(name,scope->_vpi_handle);
    }
    if(pyvpi_CheckError())
       return NULL;

    if(ans == NULL) {
        PyErr_Format(VpiError,  "Can't get right handle by name :\"%s\"!", name);
        return NULL;
    }
    //Py_XDECREF(scope);
    //printf("SCOPE refere count: %d\n", Py_REFCNT(scope));
    oans = (p_pyvpi_handle) _pyvpi_handle_New(ans);
    Py_XINCREF(oans);
    return (PyObject *)oans;
}
/* 
 * XXTERN vpiHandle  vpi_handle_by_index PROTO_PARAMS((vpiHandle object,
 *                                                     PLI_INT32 indx));
 */
static PyObject* 
pyvpi_HandleByIndex(PyObject *self, PyObject *args)
{
    p_pyvpi_handle object,oans;
    PLI_INT32 indx;
    vpiHandle ans;
    if (!PyArg_ParseTuple(args, "Ok", &object,&indx))
    {
        PyErr_SetString(VpiError,  "Error args, must be (pyvpi.Handle,long).");
        return NULL;
    }
    if (!PyObject_TypeCheck(object,&pyvpi_handle_Type)) {
        PyErr_SetString(VpiError,  "Error args, must be (pyvpi.Handle,long).");
        return NULL;
    }
    else {
        ans = vpi_handle_by_index(object->_vpi_handle,indx);
    }
    if(pyvpi_CheckError())
       return NULL;
    if(ans == NULL) {
        PyErr_Format(VpiError,  "Can't get right handle by index : %d.", indx);
        return NULL;
    }
    oans = (p_pyvpi_handle) _pyvpi_handle_New(ans);
    return (PyObject *)oans;  
}

/* for traversing relationships */
/*
    XXTERN vpiHandle  vpi_handle          PROTO_PARAMS((PLI_INT32 type,
                                                        vpiHandle refHandle));
*/
static PyObject* 
pyvpi_Handle(PyObject *self, PyObject *args)
{
    p_pyvpi_handle refHandle,oans;
    PLI_INT32 type;
    vpiHandle ans;   
    if (!PyArg_ParseTuple(args, "iO", &type,&refHandle))
    {
        PyErr_SetString(VpiError,  "Error args, must be (int,pyvpi.Handle).");
        return NULL;
    }
    if (!PyObject_TypeCheck(refHandle,&pyvpi_handle_Type)) {
        PyErr_SetString(VpiError,  "Error args, must be (long,pyvpi.Handle).");
        return NULL;    // TBD
    }
    else {
        ans = vpi_handle(type,refHandle->_vpi_handle);
    }
    if(pyvpi_CheckError())
       return NULL;
    if(ans == NULL) {
        PyErr_Format(VpiError,  "There is not relation between %d and "FADDR_MARCO".",
            type, refHandle);
        return NULL;
    }
    oans = (p_pyvpi_handle) _pyvpi_handle_New(ans);
    Py_XINCREF(oans);
    return (PyObject *)oans;   
}
/*
    XXTERN vpiHandle  vpi_handle_multi    PROTO_PARAMS((PLI_INT32 type,
                                                        vpiHandle refHandle1,
                                                        vpiHandle refHandle2,
                                                        ... ));
*/
//Can port this function now, this will be changed in future.
/*
    XXTERN vpiHandle  vpi_iterate         PROTO_PARAMS((PLI_INT32 type,
                                                        vpiHandle refHandle));
*/
static PyObject* 
pyvpi_Iterate(PyObject *self, PyObject *args)
{
    PLI_INT32 type;
    p_pyvpi_handle refHandle,oans;
    vpiHandle ans;
    if (!PyArg_ParseTuple(args, "iO", &type,&refHandle))
    {
        PyErr_SetString(VpiError,  "Error args, must be (int,pyvpi.Handle).");
        return NULL;
    }
    if (!PyObject_TypeCheck(refHandle, &pyvpi_handle_Type)) {
        pyvpi_trace("iterate 's 2nd arg is "
                    "not pyvpi.Handle type, trade refHandle as NULL.\n");
        ans = vpi_iterate(type, NULL);
    }
    else {
        ans = vpi_iterate(type,refHandle->_vpi_handle);
    }

    if(pyvpi_CheckError())
       return NULL;

    if(ans == NULL) {
        PyErr_Format(VpiError,  "Can't get right iterator in handle: "FADDR_MARCO".",
            refHandle);
        return NULL;
    }

    oans = (p_pyvpi_handle) _pyvpi_handle_New(ans);
    Py_XINCREF(oans);
    return (PyObject *)oans;   
}

/* 
    XXTERN vpiHandle  vpi_scan            PROTO_PARAMS((vpiHandle iterator));
*/
static PyObject* 
pyvpi_Scan(PyObject *self, PyObject *args)
{
    p_pyvpi_handle iterator,oans;
    vpiHandle ans;
    if (!PyArg_ParseTuple(args, "O", &iterator))
    {
        PyErr_SetString(VpiError,  "Error args, must be (pyvpi.Handle).");
        return NULL;
    }
    if (!PyObject_TypeCheck(iterator,&pyvpi_handle_Type)) {
        PyErr_SetString(VpiError,  "Error args, must be (pyvpi.Handle).");
        return NULL;
    }

    ans = vpi_scan(iterator->_vpi_handle);
    if(pyvpi_CheckError())
        return NULL;
    if(ans != NULL) {
        oans = (p_pyvpi_handle) _pyvpi_handle_New(ans);
    }
    else {
        pyvpi_verbose("pyvpi.Handle->Handle is "
                    "release,ptr is "FADDR_MARCO".\n", iterator->_vpi_handle);
        iterator->is_free = 1;
        Py_XINCREF(Py_None);
        return Py_None;
    }
    return (PyObject *)oans;   
}

/* for processing properties */
/*
    XXTERN PLI_INT32  vpi_get             PROTO_PARAMS((PLI_INT32 property,
                                                        vpiHandle object));
    
    XXTERN PLI_INT64  vpi_get64           PROTO_PARAMS((PLI_INT32 property,
                                                        vpiHandle object));
    XXTERN PLI_BYTE8 *vpi_get_str         PROTO_PARAMS((PLI_INT32 property,
                                                        vpiHandle object));
*/
static PyObject* 
pyvpi_Get(PyObject *self, PyObject *args)
{
    PLI_INT32 property;
    p_pyvpi_handle object;
    PLI_INT32 ans;
    if (!PyArg_ParseTuple(args, "iO", &property,&object))
    {
        PyErr_SetString(VpiError,  "Error args, must be (int,pyvpi.Handle).");
        return NULL;
    }
    if (!PyObject_TypeCheck(object,&pyvpi_handle_Type)) {
        PyErr_SetString(VpiError,  "Error args, must be (int,pyvpi.Handle).");
        return NULL; //TBD
    }

    ans = vpi_get(property,object->_vpi_handle);
    if(pyvpi_CheckError())
       return NULL;
    return Py_BuildValue("I", ans);
}

static PyObject* 
pyvpi_Get64(PyObject *self, PyObject *args)
{
    PLI_INT32 property;
    p_pyvpi_handle object;
    PLI_INT64 ans;
    if (!PyArg_ParseTuple(args, "iO", &property,&object))
    {
        PyErr_SetString(VpiError,  "Error args, must be (int,pyvpi.Handle).");
        return NULL;
    }
    if (!PyObject_TypeCheck(object,&pyvpi_handle_Type)) {
        PyErr_SetString(VpiError,  "Error args, must be (int,pyvpi.Handle).");
        return NULL; //TBD
    }

    ans = vpi_get(property,object->_vpi_handle);
    if(pyvpi_CheckError())
       return NULL;        
    return Py_BuildValue("L", ans); //signed long int python object.
}

static PyObject* 
pyvpi_GetStr(PyObject *self, PyObject *args)
{
    PLI_INT32 property;
    p_pyvpi_handle object;
    char  *ans;
    if (!PyArg_ParseTuple(args, "iO", &property,&object))
    {
        PyErr_SetString(VpiError,  "Error args, must be (int,pyvpi.Handle).");
        return NULL;
    }
    if (!PyObject_TypeCheck(object,&pyvpi_handle_Type)) {
        PyErr_SetString(VpiError,  "Error args, must be (int,pyvpi.Handle).");
        return NULL; //TBD
    }

    ans = vpi_get_str(property,object->_vpi_handle);
    if(pyvpi_CheckError())
       return NULL;
    return Py_BuildValue("s", ans);
}

/*
    vpiHandle  vpi_register_cb     (p_cb_data cb_data_p);
    PLI_INT32  vpi_remove_cb       (vpiHandle cb_obj);
    void       vpi_get_cb_info     (vpiHandle object, p_cb_data cb_data_p);
    vpiHandle  vpi_register_systf  (p_vpi_systf_data   systf_data_p);
    void       vpi_get_systf_info  (vpiHandle object, p_vpi_systf_data   systf_data_p);
*/
static PyObject* 
pyvpi_RegisterCb(PyObject *self, PyObject *args) 
{                                                                  //the args of vpi_remove_cb and vpi_get_cb_info.
    p_pyvpi_cbdata  cbdata;
    vpiHandle  ans;
    p_pyvpi_handle oans; 
    if (!PyArg_ParseTuple(args, "O", &cbdata))
    {
        PyErr_SetString(VpiError,  "Error args, must be (pyvpi.CbData).");
        return NULL;
    }
    Py_XINCREF(cbdata);    /* Must incref the cb information */
    ans = vpi_register_cb(&cbdata->_vpi_cbdata);
    if(pyvpi_CheckError())
        return NULL;
    oans = (p_pyvpi_handle) _pyvpi_handle_New(ans);
    Py_XDECREF(cbdata->cb_h);
    Py_XINCREF(oans);
    cbdata->cb_h =  (PyObject *)oans;
    Py_XINCREF(oans);
    return (PyObject *)oans;   
}

static PyObject* 
pyvpi_RemoveCb(PyObject *self, PyObject *args)
{
    p_pyvpi_cbdata  cbdata;
    p_pyvpi_handle  cbhandle;
    PLI_INT32  ans;
    if (!PyArg_ParseTuple(args, "O", &cbdata))
    {
        PyErr_SetString(VpiError,  "Error args, must be (pyvpi.CbData).");
        return NULL;
    }

    if (PyObject_TypeCheck(cbdata,&pyvpi_cbdata_Type)) {
        cbhandle = (p_pyvpi_handle) cbdata->cb_h;
    }
    else {
        PyErr_SetString(VpiError,  "Error args, must be (pyvpi.CbData).");
        return NULL;
    }
    ans = vpi_remove_cb(cbhandle->_vpi_handle);
    if(pyvpi_CheckError())
        return NULL;
    cbhandle->is_free = 1;
    Py_XDECREF(cbdata->cb_h);
    pyvpi_verbose("pyvpi.Handle->Handle is "
                    "release,ptr is "FADDR_MARCO".\n", cbhandle->_vpi_handle);
    Py_XDECREF(cbdata);    /* Remove cbdata reference! */      
    return Py_BuildValue("i", ans);
}

static PyObject* 
pyvpi_GetCbInfo(PyObject *self, PyObject *args)
{
     //There is no use to port this function;
     //TBD
    pyvpi_warning("pyvpi.getCbInfo is not allowed "
                "used in this version!\n");
    Py_XINCREF(Py_None);
    return Py_None;
//# p_pyvpi_handle  object,trgobj;
//# p_pyvpi_cbdata  cbdata;
//# PyObject*       pdict = DumbDict;
//# PyObject*       ptpl = DumbTuple;
//# if (!PyArg_ParseTuple(args, "O", &object))
//# {
//#     PyErr_SetString(VpiError,  "Error args, must be (pyvpi._vpiHandle).");
//#     return NULL;
//# }
//# //Initial cbdata;
//# cbdata = (p_pyvpi_cbdata) pyvpi_cbdata_New(&pyvpi_cbdata_Type,ptpl,pdict);
//# vpi_get_cb_info(object->_vpi_handle,&cbdata->_vpi_cbdata);
//# // Add trgobj info.    
//# trgobj = (p_pyvpi_handle) _pyvpi_handle_New(cbdata->_vpi_cbdata.obj);
//# //Initial cbData...
//# PyDict_SetItemString(pdict,"trgobj",(PyObject*) trgobj);
//# Py_XDECREF(trgobj);
//# pyvpi_cbdata_Init(cbdata,ptpl,pdict);    
//# Py_XDECREF(ptpl);
//# Py_XDECREF(pdict);
//# if(pyvpi_CheckError())
//#    return NULL;
//# return (PyObject*) cbdata;
 }

static PyObject*
pyvpi_RegisterSysTf(PyObject *self, PyObject *args) 
{
    s_pyvpi_systfdata*  systfdata;
    vpiHandle  ans;
    if (!PyArg_ParseTuple(args, "O", &systfdata))
    {
        PyErr_SetString(VpiError,  "Error args, must be (pyvpi.SysTfData).");
        return NULL;
    }
    ans = vpi_register_systf(&systfdata->_vpi_systfdata);
    if(pyvpi_CheckError())
       return NULL;
    Py_XINCREF(systfdata); //Always increment systfdata.
    return _pyvpi_handle_New(ans);
}

static PyObject* 
pyvpi_GetSysTfInfo(PyObject *self, PyObject *args)
{
    //There is no use to port this function;
    pyvpi_warning("pyvpi.getSysTfInfo is not allowed "
                 "used in this version!\n");
    Py_XINCREF(Py_None);
    return Py_None;
}

/* value processing
void       vpi_get_value       PROTO_PARAMS((vpiHandle expr,
                                             p_vpi_value value_p));
vpiHandle  vpi_put_value       PROTO_PARAMS((vpiHandle object,
                                             p_vpi_value value_p,
                                             p_vpi_time time_p,
                                             PLI_INT32 flags));
void       vpi_get_value_array PROTO_PARAMS((vpiHandle object,
                                             p_vpi_arrayvalue arrayvalue_p,
                                             PLI_INT32 *index_p,
                                             PLI_UINT32 num));
void       vpi_put_value_array PROTO_PARAMS((vpiHandle object,
                                             p_vpi_arrayvalue arrayvalue_p,
                                             PLI_INT32 *index_p,
                                             PLI_UINT32 num));    
*/
static PyObject * 
pyvpi_PutValue(PyObject *self, PyObject *args)
{
    p_pyvpi_handle  handle,oans; 
    p_pyvpi_value   value;
    p_pyvpi_time    time = (p_pyvpi_time) Py_None;
    PLI_INT32       flags = vpiNoDelay;
    vpiHandle       ans;
    if (!PyArg_ParseTuple(args, "OO|Oi", &handle, &value, &time, &flags))
    {
        PyErr_SetString(VpiError,  "Error args, must be (pyvpi.Handle,pyvpi.Value).");
        return NULL;
    }
    if(Py_TYPE(handle) != &pyvpi_handle_Type) {    
        PyErr_SetString(VpiError,  "Error args, 1st arg must be pyvpi.Handle.");
        return NULL;
    }
    if(Py_TYPE(value) != &pyvpi_value_Type) {
        pyvpi_debug("2nd arg of putValue is not pyvpi.Vaule, "
                    "trade it as NULL");
        value = NULL;
    }
    if(Py_TYPE(time) != &pyvpi_time_Type) {    
        //PyErr_SetString(VpiError,  "Error args, 3nd arg must be pyvpi.Time.");
        //return NULL;
        pyvpi_debug("3nd arg of putValue is not pyvpi.Time, "
                    "trade it as NULL");
        time = NULL;
    }
    // printf("******** handle is %d\n", handle->_vpi_handle);
    ans = vpi_put_value(handle->_vpi_handle,
        value == NULL? NULL : &value->_vpi_value,
        time  == NULL? NULL : &time->_vpi_time,
        flags);
    // printf("try put value \n");
    if(pyvpi_CheckError())
    {
        return NULL;
    }
    if(ans == NULL) {
        Py_XINCREF(Py_None);
        return Py_None;
    }
    oans = (p_pyvpi_handle) _pyvpi_handle_New(ans);
    Py_XINCREF(oans);
    return (PyObject *)oans; 
}

static PyObject *
pyvpi_GetValue(PyObject *self, PyObject *args)
{
    /*  Describe :
     *  This function just update the fields of pyvpi.Value;
     * */
    p_pyvpi_handle  handle; 
    p_pyvpi_value   value;
    PLI_UINT32      blen = 0;
    if (!PyArg_ParseTuple(args, "OO", &handle, &value))
    {
        PyErr_SetString(VpiError,  "Error args, must be (pyvpi.Handle,pyvpi.Value).");
        return NULL;
    }
    if(Py_TYPE(handle) != &pyvpi_handle_Type) {    
        PyErr_SetString(VpiError,  "Error args, 1st arg must be pyvpi.Handle.");
        return NULL;
    }
    if(Py_TYPE(value) != &pyvpi_value_Type) {    
        PyErr_SetString(VpiError,  "Error args, 2nd arg must be pyvpi.Value.");
        return NULL;
    }
    if(value->fixed_handle != NULL && 
        value->fixed_handle->_vpi_handle != handle->_vpi_handle){
        PyErr_SetString(VpiError,  "Can't put different handle value to fixed handle pyvpi.Value.");
        return NULL;
    }
    if(value->_vpi_value.format == vpiVectorVal) {
        p_pyvpi_vector pvec;
        blen = vpi_get(vpiSize,handle->_vpi_handle);
        if(pyvpi_CheckError()){
            return NULL;
        }
        /* Update vetcotr cache to store the value.*/        
        pvec = (p_pyvpi_vector) value->obj;
        if(blen > pvec->size) {
            pvec->size = blen;
            pyvpi_vector_update_cache(pvec);
        }
    }
    vpi_get_value(handle->_vpi_handle,&value->_vpi_value);
    pyvip_value_update_value(value,&value->_vpi_value,blen);
    if(pyvpi_CheckError())
        return NULL;
    Py_XINCREF(Py_None);
    return Py_None;
}

static PyObject *
pyvpi_GetTime(PyObject *self, PyObject *args)
{
    p_pyvpi_handle  handle = (p_pyvpi_handle) Py_None;
    p_pyvpi_time    time = (p_pyvpi_time) Py_None;
    if (!PyArg_ParseTuple(args, "O|O", &time, &handle))
    {
        PyErr_SetString(VpiError,  "Error args, must be (pyvpi.Time, pyvpi.Handle).");
        return NULL;
    }
    if(Py_TYPE(time) != &pyvpi_time_Type) {
        PyErr_SetString(VpiError,  "Error args, 1st arg must be pyvpi.Time.");
        return NULL;
    }
    if(Py_TYPE(handle) != &pyvpi_handle_Type) {
        vpi_get_time(0,&time->_vpi_time);
    }
    else 
    {        
        vpi_get_time(handle->_vpi_handle,&time->_vpi_time);
    }
    if(pyvpi_CheckError())
        return NULL;
    Py_XINCREF(Py_None);
    return Py_None;
}

static PyObject* 
pyvpi_Control(PyObject *self, PyObject *args)
{
    PLI_INT32 op;
    if (!PyArg_ParseTuple(args, "k", &op))
    {
        PyErr_SetString(VpiError,  "Error args, must be (int).");
        return NULL;
    }   
    return Py_BuildValue("i",vpi_control(op));    
}

static PyObject*
pyvpi_SetDebugLevel(PyObject *self, PyObject *args)
{
    PLI_INT32 new_level = PRINT_NOTE;
    if (!PyArg_ParseTuple(args, "k", &new_level))
    {
        PyErr_SetString(VpiError,  "Error args, must be (int).");
        return NULL;
    }
    print_level = new_level;
    Py_XINCREF(Py_None);
    return Py_None;
}

/*
    \brief createValueFromMMap
    @input   :
        handle :    value for store handle.
        format :    value format.
        saddr  :    buffer start addr.
        eaddr  :    buffer end addr.
    @return  :
        (Value,newsaddr)  : the new Value object and the new saddr.
    In some suituation,the value size always keep unchangeable,these values only used
    the same handles, so we can swap value fastly by this previlege between process 
    by mmap.
    |----------|-----------|-----------------------|
    sa  value       oval   na       rest           ea
    sa      : saddr;
    value   : value object;
    oval    : like string buffer,vector,time object;
    na      : newsaddr;
    da      : eaddr.
 */
static PyObject*
pyvpi_CreateValueFromMMap(PyObject *self, PyObject *args)
{
    p_pyvpi_handle   handle;
    PLI_INT32   format;
#ifdef __LP64__
    PLI_UINT64  saddr;  //void* point.
    PLI_UINT64  eaddr;  //void* point.
#else
    PLI_UINT32  saddr;  //void* point.
    PLI_UINT32  eaddr;  //void* point.
#endif
    p_pyvpi_value  value;
    
    PLI_UINT32   cache_size;  //vector,string buffer.
  //PLI_UINT32   value_size;  //value size.
  //PLI_UINT32   size;        //total size.
    unsigned int i;
#ifdef __LP64__
    if (!PyArg_ParseTuple(args, "OiKK",&handle,&format,&saddr,&eaddr)){
#else
    if (!PyArg_ParseTuple(args, "Oikk",&handle,&format,&saddr,&eaddr)){
#endif
        PyErr_SetString(VpiError,  "Error args, must be (Handle,format(int), saddr(int),eaddr(int)).");
        return NULL;
    }
    if(Py_TYPE(handle) != &pyvpi_handle_Type) {
        PyErr_SetString(VpiError,  "1st arg must be Handle.");
        return NULL;
    }
    saddr = ((saddr-1)/PYVPI_ALIGN + 1) * PYVPI_ALIGN;
    //value_size = sizeof(s_pyvpi_value);
    //value_size = (value_size/PYVPI_ALIGN + 1) * PYVPI_ALIGN;
    //size = value_size;

    /* Calc other object size. */
    switch (format) {
    /* all string values */
    case vpiBinStrVal:
    case vpiOctStrVal:
    case vpiDecStrVal:
    case vpiHexStrVal:
    case vpiStringVal:
    case vpiVectorVal:
        cache_size = vpi_get(vpiSize,((p_pyvpi_handle)handle)->_vpi_handle) + 1;        
        if(pyvpi_CheckError())
            return NULL;
        /* In order to keep vector at size < 8, cache_size must big equal than 8;
         */
        if(cache_size < 8)
            cache_size = 8;
        //size += cache_size;
        break;
    case vpiScalarVal:
    case vpiIntVal:
    case vpiRealVal:
    case vpiStrengthVal:
        /*
        cache_size = (sizeof(s_pyvpi_strengthval)/PYVPI_ALIGN + 1) * PYVPI_ALIGN;
        size += cache_size;
        break;
        */
    case vpiTimeVal:
        /*
        cache_size = (sizeof(s_pyvpi_time)/PYVPI_ALIGN + 1) * PYVPI_ALIGN;
        size += cache_size;
        break;
        */
        PyErr_SetString(VpiError,"The createValueFromMMap don't support"
            "vpiScalarVal,vpiIntVal,vpiRealVal,vpiStrengthVal,vpiTimeVal!"
            );
        return NULL;
    case vpiObjTypeVal: case vpiSuppressVal:
        PyErr_SetString(VpiError,"The format of pyvpi.Value not "
            "support vpiObjTypeVal and vpiSuppressVal."
            );
        return NULL;
    default :
        PyErr_SetString(VpiError,"The format of pyvpi.Value must be "
            "vpi[[Bin,Oct,Dec,Hex]Str,Scalar,Int,Real,String,Vector,"
            "Strength,Suppress,Time,ObjType]Val.");
        return NULL;
    }

    if(saddr + cache_size >eaddr) {
        PyErr_Format(VpiError,  "Can't alloc enough buffer(%d) between saddr(%d) and eaddr(%d).",
            cache_size,saddr,eaddr);
        return NULL;
    }
    /* Do memory initial. */
    for(i = 0; i < cache_size;i++){
        *(char *)(saddr + i) = 0;
    }

    /* Initial value in buffer. */
    value = (p_pyvpi_value)pyvpi_value_Type.tp_alloc(&pyvpi_value_Type, 0);
    if(value == NULL)
        return NULL;
    value->_vpi_value.format = format;       
    /*
        Do value initial.
     */
    Py_XINCREF(handle);
    value->fixed_handle = handle;
    value->cache_size   = cache_size;
        switch (format) {
    /* all string values */
    case vpiBinStrVal:
    case vpiOctStrVal:
    case vpiDecStrVal:
    case vpiHexStrVal:
    case vpiStringVal:
	//	value->obj    = PyString_FromString("");
    // zony add for py3
    	value->obj    = PyUnicode_FromString("");
        value->_vpi_value.value.str = (char *) saddr;
        break;
    /* Don't support!
    case vpiScalarVal:
        value->obj    = PyInt_FromLong(vpi0);        
        break;
    case vpiIntVal:
        value->obj    = PyInt_FromLong(0);
        break;
    case vpiRealVal:
        value->obj    = PyFloat_FromDouble(0.0);
        break;
    */
    case vpiVectorVal:
        /* For vector, we only use saddr to store vpi_vector struct,not for p_pyvpi_vector.*/
        value->obj    = pyvpi_vector_New(&pyvpi_vector_Type,DumbTuple,DumbDict);
        pyvpi_vector_Init((p_pyvpi_vector)value->obj,DumbTuple,DumbDict);
        ((p_pyvpi_vector)value->obj)->size = vpi_get(vpiSize,((p_pyvpi_handle)handle)->_vpi_handle);
        ((p_pyvpi_vector)value->obj)->cache_size = cache_size/sizeof(s_vpi_vecval);
        free(((p_pyvpi_vector)value->obj)->cache_ptr);
        ((p_pyvpi_vector)value->obj)->cache_ptr = (p_vpi_vecval) saddr;
        ((p_pyvpi_vector)value->obj)->_vpi_vector = (p_vpi_vecval) saddr;
        value->_vpi_value.value.vector = (p_vpi_vecval) saddr;
        break;
    /* Don't support.
    case vpiStrengthVal:
        value->obj    = (PyObject *) saddr;
        PyObject_Init(value->obj,&pyvpi_strengthval_Type);
        value->_vpi_value.value.strength = &((p_pyvpi_strengthval)value->obj)->_vpi_strengthval;
        break;
    case vpiTimeVal:
        value->obj    = (PyObject *) saddr;
        PyObject_Init(value->obj,&pyvpi_time_Type);
        value->_vpi_value.value.time = &((p_pyvpi_time)value->obj)->_vpi_time;
        break;    
    case vpiObjTypeVal: case vpiSuppressVal:
        PyErr_SetString(VpiError,"The format of pyvpi.Value not "
            "support vpiObjTypeVal and vpiSuppressVal."
            );
        return NULL;
    default :
        PyErr_SetString(VpiError,"The format of pyvpi.Value must be "
            "vpi[[Bin,Oct,Dec,Hex]Str,Scalar,Int,Real,String,Vector,"
            "Strength,Suppress,Time,ObjType]Val.");
        return NULL;
    */
    }
    saddr += cache_size;    
#ifdef __LP64__
    return Py_BuildValue("(OK)",value,saddr);
#else
    return Py_BuildValue("(Ok)",value,saddr);
#endif
}


// zony added here
// get the timescale 
static PyObject *
pyvpi_GetTimeScale(PyObject *self, PyObject *args)
{
    p_pyvpi_handle  handle = (p_pyvpi_handle) Py_None;
    PLI_INT32 property;
    PLI_INT32 ans;
    if (!PyArg_ParseTuple(args, "i|O", &property, &handle))
    {
        PyErr_SetString(VpiError,  "Error args, must be (int, pyvpi.Handle).");
        return NULL;
    }

    if(Py_TYPE(handle) != &pyvpi_handle_Type) {
        ans = vpi_get(property,NULL);
    }
    else 
    {        
        ans = vpi_get(property,handle->_vpi_handle);
    }
    if(pyvpi_CheckError())
        return NULL;
    return Py_BuildValue("I",ans);
}

static PyMethodDef pyvpi_Methods[] = {
   /* for obtaining handles */
   {"handleByName",    pyvpi_HandleByName,     METH_VARARGS,   "vpiHandle  vpi_handle_by_name (PLI_BYTE8 *name, vpiHandle scope)."},
   {"handleByIndex",   pyvpi_HandleByIndex,    METH_VARARGS,   "vpiHandle  pyvpi_HandleByIndex (vpiHandle object, PLI_INT32 indx)."},
   /* for traversing relationships */
   {"handle",          pyvpi_Handle,           METH_VARARGS,   "vpiHandle  vpi_handle   (PLI_INT32 type, vpiHandle refHandle)"},
   //{"HandleMulti",     pyvpi_HandleMulti,      METH_VARARGS,   "vpiHandle  vpi_handle_multi    (PLI_INT32 type, vpiHandle refHandle1, vpiHandle refHandle2, ... )"},
   {"iterate",         pyvpi_Iterate,          METH_VARARGS,   "vpiHandle  vpi_iterate (PLI_INT32 type, vpiHandle refHandle)"},
   {"scan",            pyvpi_Scan,             METH_VARARGS,   "vpiHandle  vpi_scan    (vpiHandle iterator)"},
   /* for processing data*/
   {"getValue",        pyvpi_GetValue,         METH_VARARGS,   "void       vpi_get_value       (vpiHandle expr, p_vpi_value value_p)."},
   {"putValue",        pyvpi_PutValue,         METH_VARARGS,   "vpiHandle  vpi_put_value       (vpiHandle expr, p_vpi_value value_p, p_vpi_time time_p, PLI_INT32 flags)."},
   /* for processing properties */
   {"get",             pyvpi_Get,              METH_VARARGS,   "PLI_INT32  vpi_get             (PLI_INT32 property, vpiHandle object)."},
   {"get64",           pyvpi_Get64,            METH_VARARGS,   "PLI_INT64  vpi_get64           (PLI_INT32 property, vpiHandle object)."},
   {"getStr",          pyvpi_GetStr,           METH_VARARGS,   "PLI_BYTE8 *vpi_get_str         (PLI_INT32 property, vpiHandle object)."},
   {"registerCb",      pyvpi_RegisterCb,       METH_VARARGS,   "vpiHandle  vpi_register_cb     (p_cb_data cb_data_p)."},
   {"removeCb",        pyvpi_RemoveCb,         METH_VARARGS,   "PLI_INT32  vpi_remove_cb       (vpiHandle cb_obj)."},
   {"getCbInfo",       pyvpi_GetCbInfo,        METH_VARARGS,   "void       vpi_get_cb_info     (vpiHandle object, <out>p_cb_data cb_data_p)."},
   {"registerSysTf",   pyvpi_RegisterSysTf,    METH_VARARGS,   "vpiHandle  vpi_register_systf  (p_systf_data systf_data_p)."},
   {"getSysTfInfo",    pyvpi_GetSysTfInfo,     METH_VARARGS,   "void       vpi_get_systf_info  (vpiHandle object, <out>p_systf_data systf_data_p)."},
   {"printf",          pyvpi_Print,            METH_VARARGS,   "print function for vpi_printf"},
   {"getTime",         pyvpi_GetTime,          METH_VARARGS,   "void       vpi_get_time      (p_vpi_time time,vpiHandle obj)."},
   {"control",         pyvpi_Control,          METH_VARARGS,   "contorl"},
   {"getTimeScale",    pyvpi_GetTimeScale,     METH_VARARGS,   "Get time scale of the simulation."},
   /* -- Utils functions --*/
   {"setDebugLevel",        pyvpi_SetDebugLevel,       METH_VARARGS,   "set pyvpi debug print level."},
   {"createValueFromMMap",  pyvpi_CreateValueFromMMap, METH_VARARGS,   "crete value from buffer."},
    // zonyzhao add
    {"setSvScopeByName", pyvpi_setsvscopebyname, METH_VARARGS, "set svscope by name."},
    {"callwithsvscopebyname", pyvpi_callwithsvscopebyname, METH_VARARGS, "call export sv function under a scope."},
    {"getSvScopeName", pyvpi_getSvScopeName, METH_VARARGS, ""},
   {NULL, NULL, 0, NULL}        /* Sentinel */
};

/*
  pyvpi log printf functions.
 */
#ifndef PYVPI_LOG_FUNC
#define PYVPI_LOG_FUNC(pl,PL)\
PLI_INT32 \
    pyvpi_##pl(PLI_BYTE8 * format, ...)\
{\
    va_list va;\
    PLI_INT32 retval = 0;\
    if(print_level <= PRINT_##PL) {\
        vpi_printf(#PL" : ");\
        va_start(va, format);\
        retval = vpi_vprintf(format, va);\
        va_end(va);\
    }\
    return retval;\
}
#endif

PYVPI_LOG_FUNC(verbose,VERBOSE)
PYVPI_LOG_FUNC(debug,DEBUG)
PYVPI_LOG_FUNC(trace,TRACE)
PYVPI_LOG_FUNC(note,NOTE)
PYVPI_LOG_FUNC(warning,WARNING)
PYVPI_LOG_FUNC(error,ERROR)
PYVPI_LOG_FUNC(fatal,FATAL)

#ifndef PYVPI_TYPE_READY
#define PYVPI_TYPE_READY(vpi_type,name) \
    if (PyType_Ready(&vpi_type) < 0) \
    {\
    pyvpi_error(#vpi_type" is not Ready.\n"); \
        return NULL;\
    }\
    pyvpi_verbose(#vpi_type" is "FADDR_MARCO".\n",&vpi_type);\
    Py_XINCREF(&vpi_type);\
    PyModule_AddObject(m, #name, (PyObject *)&vpi_type)    

#endif

// zony add py3
static struct PyModuleDef moduledef = 
{
	PyModuleDef_HEAD_INIT,
	"pyvpi",
	NULL,
	-1,
	pyvpi_Methods
};

//Module initial here
PyMODINIT_FUNC PyInit_pyvpi(void)
{
    PyObject *m;
 
    //Initial the module.
    // zony add py3
    // m = Py_InitModule("pyvpi", pyvpi_Methods);
    m = PyModule_Create(&moduledef);
    if (m == NULL)
        return NULL;

    PYVPI_TYPE_READY(pyvpi_value_Type,Value);
    PYVPI_TYPE_READY(pyvpi_cbdata_Type,CbData);
    PYVPI_TYPE_READY(pyvpi_time_Type,Time);
    PYVPI_TYPE_READY(pyvpi_strengthval_Type,Strength);
    PYVPI_TYPE_READY(pyvpi_vector_Type,Vector);
    PYVPI_TYPE_READY(pyvpi_delays_Type,Delays);
    PYVPI_TYPE_READY(pyvpi_systfdata_Type,SysTfData);
    PYVPI_TYPE_READY(pyvpi_handle_Type,Handle);

    //Add vpi Error in pyvpi module.
    VpiError = PyErr_NewException("pyvpi.vpiError", NULL, NULL);
    Py_XINCREF(VpiError);
    PyModule_AddObject(m, "vpiError", VpiError);
    //return;
    //Add python Error in pyvpi module.
    PyError = PyErr_NewException("pyvpi.PyError", NULL, NULL);
    Py_XINCREF(PyError);
    PyModule_AddObject(m, "PyError", PyError);
    
    DumbTuple   =   PyTuple_New(0);
    DumbDict    =   PyDict_New();
    int rt;
    rt = PyModule_AddObject(m,"DumbTuple",DumbTuple);
    printf("init module, rt = %d\n",rt);
    PyModule_AddObject(m,"DumbDict",DumbDict);
    return m;
}

//============================================================================
PLI_INT32 pyvpi_StartSim(p_cb_data cb_data_p)
{
    // char *pyvpi_start =    "+pyvpi+start=";    //When this sim is start , execute what?
    // s_vpi_vlog_info info;
    // if(vpi_get_vlog_info(&info)){
    //     int i = 0;
    //     char *p = pyvpi_start,*q='\0';
    //     for(i = 0; i<info.argc; i++) {
    //         q = info.argv[i];
    //         p = pyvpi_start;
    //         for(;*p != '\0' && *q != '\0';p++,q++){
    //             if(*p != *q) break;
    //         }    
    //         if(*p == '\0'){
    //             FILE *fp;
    //             fp = fopen(q,"r");
    //             // py_fp = PyFile_FromString(q, "r");
    //             // zony add py3
    //             PyRun_SimpleFile(fp,q);
    //             break;
    //         }
    //     }
    // }
    // PyRun_SimpleString("import background_zmq_ipython");
    // PyRun_SimpleString("import time");

    // Py_BEGIN_ALLOW_THREADS
    // PyRun_SimpleString("background_zmq_ipython.init_ipython_kernel()");
    // PyRun_SimpleString("time.sleep(10)");
    // Py_END_ALLOW_THREADS

    // gtstate = PyEval_SaveThread();
    // Py_BEGIN_ALLOW_THREADS
    // gtstate = PyEval_SaveThread();
    glstate = PyGILState_Ensure();
    char *TB = NULL;
    printf("*************\n");
    TB = getenv("PYVPI_TB");
    printf("current tb is %s\n", TB);
    if(!TB)
    {
        printf("no Python TB found in PYVPI_TB\n");
    }
    else
    {
        FILE* py_fp;
        py_fp = fopen(TB, "r");
        if(!py_fp)
            printf("No file found\n");
        else
        {
            // Py_BEGIN_ALLOW_THREADS
            // glstate = PyGILState_Ensure();
            PyRun_SimpleFile(py_fp,TB);
            // PyGILState_Release(glstate);
            // Py_END_ALLOW_THREADS
        }
    }
    
    PyGILState_Release(glstate);
    // Py_END_ALLOW_THREADS
    return 0;
}

PLI_INT32 pyvpi_EndSim(p_cb_data cb_data_p)
{
    pyvpi_debug("python begin env finalize.\n");
    // PyEval_RestoreThread(gtstate);
    // Py_Finalize();
    // printf("python end env finalize.\n");
    return 0;
}

// zony add

PLI_INT32 pyvpi_ResetSim(p_cb_data cb_data_p)
{
    // if(!Py_IsInitialized())
    // {
    //     // PyEval_RestoreThread(gtstate);
    //     Py_Finalize();
    // }
        
    //     // Py_FinalizeEx();
    // // dlopen("libvpi.so");
    // Py_Initialize();
    // // add threading support
    // if(!PyEval_ThreadsInitialized())
    // {
    //     printf("Thread reinit\n");
    //     PyEval_InitThreads();
    // }

    // gtstate = PyEval_SaveThread();

    printf("*************\n");
    printf("python end env reinitial.\n");

    // char *TB = NULL;
    // TB = getenv("PYVPI_TB");
    // printf("current tb is %s\n", TB);
    // if(!TB)
    // {
    //     printf("no Python TB found in PYVPI_TB\n");
    // }
    // else
    // {
    //     FILE* py_fp;
    //     py_fp = fopen(TB, "r");
    //     if(!py_fp)
    //         printf("No file found\n");
    //     else
    //         PyRun_SimpleFile(py_fp,TB);
    // }

    s_vpi_time  time_s;
    time_s.low = 0;
    time_s.high = 0;
    time_s.type = vpiSimTime;
    static s_cb_data cb_0_simtime;
    cb_0_simtime.reason = cbAfterDelay;
    cb_0_simtime.time = &time_s;
    cb_0_simtime.cb_rtn = pyvpi_StartSim;
    vpi_register_cb(&cb_0_simtime);
    // static s_cb_data cb_start_sim = {cbStartOfSimulation,pyvpi_StartSim};

    printf("reset python\n");
    return 0;
}
/*****************************************************************************
 * pyvpi_RegisterCallbacks
 * Registers test functions with the simulator.
 *****************************************************************************/
void pyvpi_RegisterCallbacks (void)
{
    static s_cb_data cb_start_sim = {cbStartOfSimulation,pyvpi_StartSim};
    static s_cb_data cb_end_sim   = {cbEndOfSimulation,pyvpi_EndSim};
    // zony add here
    static s_cb_data cb_reset_sim = {cbEndOfReset, pyvpi_ResetSim};
    vpi_register_cb(&cb_start_sim);
    vpi_register_cb(&cb_end_sim);
    vpi_register_cb(&cb_reset_sim);

    static s_cb_data cb_end_of_restart = {cbEndOfRestart, pyvpi_StartSim};
    vpi_register_cb(&cb_end_of_restart);

    // s_vpi_time  time_s;
    // time_s.low = 0;
    // time_s.high = 0;
    // time_s.type = vpiSimTime;
    // static s_cb_data cb_0_simtime;
    // cb_0_simtime.reason = cbAtStartOfSimTime;
    // cb_0_simtime.time = &time_s;
    // cb_0_simtime.cb_rtn = pyvpi_StartSim;
    // vpi_register_cb(&cb_0_simtime);
}

/*****************************************************************************
 * pyvpi_main
 * The main function of pyvpi, you can use $pyvpi_main in verilog to call 
 * special python scripts.
 *****************************************************************************/
PLI_INT32 
pyvpi_main( PLI_BYTE8 *user_data )
{
    vpiHandle self;
    vpiHandle arg_iter;
    vpiHandle arg;
    s_vpi_value val;
    PyObject* py_fp;

    val.format = vpiStringVal;
    self = vpi_handle(vpiSysTfCall,NULL);
    arg_iter = vpi_iterate(vpiArgument,self);
    arg =vpi_scan(arg_iter);
    if(CheckError()) {
        return -1;
    }
    vpi_get_value(arg,&val);
    FILE* fp;
    fp = fopen(val.value.str, "r");
    // svScope scope = svGetScope();
    // svSetScope(scope);
    // Py_Initialize();
    // Py_BEGIN_ALLOW_THREADS
    glstate = PyGILState_Ensure();
    PyRun_SimpleFile(fp,val.value.str);
    PyGILState_Release(glstate);
    // Py_END_ALLOW_THREADS
    return 0;
}

int 
pyvpi_dpi( char *fn )
{
    FILE* fp;
    fp = fopen(fn, "r");
    // svScope scope = svGetScope();
    // svSetScope(scope);
    // Py_Initialize();
    // Py_BEGIN_ALLOW_THREADS
    glstate = PyGILState_Ensure();
    vpi_printf("Called from scope :: %s\n\n", svGetNameFromScope(svGetScope()));
    PyRun_SimpleFile(fp,fn);
    PyGILState_Release(glstate);
    // Py_END_ALLOW_THREADS
    return 0;
}


PLI_INT32 
pyvpi_main_check( PLI_BYTE8 *user_data )
{
    vpiHandle self;
    vpiHandle arg_iter;
    vpiHandle arg;
    PLI_INT32 index = 0;
    PLI_INT32 re = 0;
    self = vpi_handle(vpiSysTfCall,NULL);
    arg_iter = vpi_iterate(vpiArgument,self);
    if(!(re = CheckError()) && arg_iter){
        while((arg =vpi_scan(arg_iter))){
            if((re = CheckError()))
                break;
            switch(index){
            case 0 :
                if(vpi_get(vpiType,arg) == vpiConstant &&
                    vpi_get(vpiConstType,arg) == vpiStringConst){
                }
                else {
                    pyvpi_fatal("The 1st of pyvpi_main must be a "
                        "path string which indicate a py file.\n");
                }
                break;
            default :
                pyvpi_fatal("In this version, pyvpi only accept one"
                    " string arg.\n");
                break;
            }
            index++;
            vpi_free_object(arg);
        }
    }
    if(index != 1) {
        pyvpi_fatal("In this version, pyvpi only/must accept one"
                    " string arg.\n");
    }
    return re;
}

/*****************************************************************************
 * pyvpi_RegisterTfs
 * Registers test functions with the simulator.
 *****************************************************************************/
void pyvpi_RegisterTfs( void )
{
    s_vpi_systf_data    systf_data;
    vpiHandle            systf_handle;
    char  *argv[]     =    {"-v"};
    char *pyvpi_load =    "+pyvpi+load=";    //When this lib is load , execute what?

    systf_data.type        = vpiSysTask;
    systf_data.sysfunctype = 0;
    systf_data.tfname      = "$pyvpi_main";
    systf_data.calltf      = pyvpi_main;
    systf_data.compiletf   = pyvpi_main_check;
    systf_data.sizetf      = 0;
    systf_data.user_data   = 0;
    systf_handle = vpi_register_systf( &systf_data );
    vpi_free_object( systf_handle );

    //We must initial Python here so we can use python register 
    //System task and function.
    //svScope scope = svGetScope();
    //svSetScope(scope);
    pyvpi_debug("python begin env initial.\n");

    // dlopen("libvpi.so");

    Py_Initialize();
    if (!PyEval_ThreadsInitialized())
    {
        PyEval_InitThreads();
    }


    pyvpi_debug("*************\n");
    pyvpi_debug("Insert parameteres\n");
    wchar_t *wargv;
    char *s = argv[0];
    size_t slen = sizeof (s);
    wargv = (wchar_t *) calloc (slen + 1, sizeof (wchar_t));
    mbstowcs (wargv, s, slen);
    PySys_SetArgv (1, &wargv);
    pyvpi_debug("python end env initial.\n");

    gtstate = PyEval_SaveThread();
    // add threading support
    // PyThreadState *save;
    // gtstate = PyEval_SaveThread();
    // glstate = PyGILState_Ensure();
    // // gtstate = PyThreadState_Get();
    // // PyObject * pModule = NULL;
    // // PyObject * pFunc = NULL;
    // // PyObject * pArgs = NULL;
    // // pArgs = Py_BuildValue("()");
    // // pModule = PyImport_ImportModule("background_zmq_ipython");
    // // pFunc = PyObject_GetAttrString(pModule, "init_ipython_kernel");
    // // PyEval_CallObject(pFunc, pArgs);
    // PyGILState_Release(glstate);
    // // removed to add scope
    // {
    //     s_vpi_vlog_info info;
    //     if(vpi_get_vlog_info(&info)){   //First try to get vlog info.
    //         int i = 0;
    //         char *p = pyvpi_load,*q=pyvpi_load;
    //         for(i = 0; i<info.argc; i++) {
    //             q = info.argv[i];
    //             p = pyvpi_load;
    //             for(;*p != '\0' && *q != '\0';p++,q++){
    //                 if(*p != *q) break;
    //             }
    //             if(*p == '\0') break;
    //         }
    //         if(*p == '\0'){
    //             /* Pass load filename from args */
    //             FILE* py_fp;
    //             py_fp = fopen(q, "r");
    //             PyRun_SimpleFile(py_fp,q);
    //         }
    //     }
    //     else {
    //         /* Default pyvpi load file. */
    //         if(access("pyvpi.load",0) == 0) {
    //             FILE* py_fp;
    //             py_fp = fopen("pyvpi.load", "r");
    //             PyRun_SimpleFile(py_fp,"pyvpi.load");
    //         }
    //     }
    // }

    // char *TB = NULL;
    // TB = getenv("PYVPI_TB");
    // printf("current tb is %s\n", TB);
    // if(!TB)
    // {
    //     printf("no Python TB found in PYVPI_TB\n");
    // }
    // else
    // {
    //     FILE* py_fp;
    //     py_fp = fopen(TB, "r");
    //     if(!py_fp)
    //         printf("No file found\n");
    //     else
    //         PyRun_SimpleFile(py_fp,TB);
    // }

}

/*****************************************************************************
 * Required structure for initializing VPI routines.
 *****************************************************************************/

void (*vlog_startup_routines[])() = {
    pyvpi_RegisterTfs,
    pyvpi_RegisterCallbacks,
    0
};
