
#include "gensrc/module.hpp"

PYBIND11_MODULE(ntcore, m)
{
  initWrapper(m);
}
