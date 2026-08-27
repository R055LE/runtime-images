#include <Python.h>

static PyObject *answer(PyObject *self, PyObject *args) {
    return PyLong_FromLong(42);
}

static PyMethodDef methods[] = {
    {"answer", answer, METH_NOARGS, "Return the contract value."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "native_contract",
    NULL,
    -1,
    methods
};

PyMODINIT_FUNC PyInit_native_contract(void) {
    return PyModule_Create(&module);
}
