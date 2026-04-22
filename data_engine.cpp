#include <iostream>
#include <fstream>
#include <cstdlib>
#include <ctime>

using namespace std;

int main() {
    // Creating a CSV file to simulate high-speed data ingestion
    ofstream dataFile("synthetic_housing_data.csv");
    
    if (!dataFile.is_open()) {
        cout << "Error opening file!" << endl;
        return 1;
    }

    // Write CSV Headers
    dataFile << "sqft,bhk,property_age,distance_to_metro,price_lakhs\n";

    // Seed the random number generator
    srand(time(0));

    // Generate 1000 rows of synthetic Gurgaon housing data
    cout << "Generating 1000 rows of housing data..." << endl;
    for (int i = 0; i < 1000; i++) {
        int sqft = rand() % 3200 + 800; // 800 to 4000 sqft
        int bhk = rand() % 4 + 1;       // 1 to 4 BHK
        int age = rand() % 20;          // 0 to 19 years old
        float metro = (rand() % 150) / 10.0 + 0.5; // 0.5 to 15.0 km
        
        // Rough pricing logic based on features
        int base_price = (sqft * 0.05) + (bhk * 10) - (age * 2) - (metro * 3);
        int final_price = base_price + (rand() % 20); // Add some market noise

        if (final_price < 30) final_price = 30; // Minimum price floor

        dataFile << sqft << "," << bhk << "," << age << "," << metro << "," << final_price << "\n";
    }

    dataFile.close();
    cout << "Data generation complete. File saved as synthetic_housing_data.csv" << endl;
    
    return 0;
}
