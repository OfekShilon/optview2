#include <iostream>
#include <vector>

// Based on Roi Barkan - "Argument passing, core guidelines and concepts" - https://www.youtube.com/watch?v=uylFACqcWYI
void scale_down(std::vector<double>& v, const double& a) {
    for (auto& item : v) {
        item /= a;
    }
}

void scale_down_example() {
    std::vector<double> v {2, 1, 2, 3, 4};
    scale_down(v, v[0]);

}

int main() {
    scale_down_example();

    return 0;
}
