#include "./another.hh"

Another::Another(int _value) : value(_value)
{
}

int Another::getValue() const
{
    return value;
}
