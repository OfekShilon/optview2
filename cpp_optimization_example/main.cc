#include <iostream>
#include "./another.hh"

int main() {
    Another a(3);
    std::cout << "Value of a is " << a.getValue() << std::endl;
    return 0;
}
