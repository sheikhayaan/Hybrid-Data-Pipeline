#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>

struct Property {
    int sqft;
    int bedrooms;
    int age_years;
    double metro_distance_km;
    double price_lakhs;
};

double compute_price_lakhs(
    int sqft,
    int bedrooms,
    int age_years,
    double metro_distance_km,
    std::mt19937& rng
) {
    const double base_price = 18.0;
    const double sqft_component = 0.105 * sqft;
    const double bedroom_component = 7.5 * bedrooms;

    const double age_multiplier = 0.72 + 0.28 * std::exp(-age_years / 9.0);
    const double metro_proximity = 1.0 / (1.0 + metro_distance_km);
    const double metro_component = 42.0 * metro_proximity;
    const double sqft_metro_interaction = 0.035 * sqft * std::pow(metro_proximity, 1.25);

    double deterministic_price =
        (base_price + sqft_component + bedroom_component) * age_multiplier +
        metro_component +
        sqft_metro_interaction;

    std::normal_distribution<double> normal_noise(0.0, 30.0);
    deterministic_price += normal_noise(rng);

    std::bernoulli_distribution outlier_event(0.055);
    if (outlier_event(rng)) {
        std::normal_distribution<double> shock(0.0, 85.0);
        deterministic_price += shock(rng);
    }

    return std::max(18.0, deterministic_price);
}

int main(int argc, char* argv[]) {
    int row_count = 1000;
    if (argc > 1) {
        try {
            row_count = std::stoi(argv[1]);
        } catch (const std::exception&) {
            std::cerr << "Invalid row count. Pass a positive integer, or omit it for 1000 rows.\n";
            return 1;
        }

        if (row_count <= 0) {
            std::cerr << "Invalid row count. Pass a positive integer, or omit it for 1000 rows.\n";
            return 1;
        }
    }

    std::cout << "Row count set to " << row_count << " (from "
              << (argc > 1 ? "command-line argument" : "default") << ")\n";

    std::mt19937 rng(42);

    std::uniform_int_distribution<int> sqft_dist(450, 3500);
    std::uniform_int_distribution<int> bedrooms_dist(1, 5);
    std::uniform_int_distribution<int> age_dist(0, 30);
    std::uniform_real_distribution<double> metro_dist(0.1, 15.0);

    std::ofstream output("synthetic_housing_data.csv");
    if (!output) {
        std::cerr << "Failed to open synthetic_housing_data.csv for writing.\n";
        return 1;
    }

    output << "sqft,bedrooms,age_years,metro_distance_km,price_lakhs\n";
    output << std::fixed << std::setprecision(2);

    for (int i = 0; i < row_count; ++i) {
        Property property{};
        property.sqft = sqft_dist(rng);
        property.bedrooms = bedrooms_dist(rng);
        property.age_years = age_dist(rng);
        property.metro_distance_km = metro_dist(rng);
        property.price_lakhs = compute_price_lakhs(
            property.sqft,
            property.bedrooms,
            property.age_years,
            property.metro_distance_km,
            rng
        );

        output << property.sqft << ','
               << property.bedrooms << ','
               << property.age_years << ','
               << property.metro_distance_km << ','
               << property.price_lakhs << '\n';
    }

    std::cout << "Generated " << row_count << " rows in synthetic_housing_data.csv\n";
    std::cout << "Note: prices intentionally include non-linear age depreciation, "
              << "diminishing metro-proximity effects, a sqft/metro interaction, "
              << "Gaussian noise, and injected outliers.\n";
    std::cout << "This dataset is for systems integration and pipeline demonstration, "
              << "not real-world valuation accuracy.\n";

    return 0;
}
