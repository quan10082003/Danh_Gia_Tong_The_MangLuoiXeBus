echo "run test_otp_scoring"
py -m tests.modules.bus_scoring.test_otp_scoring

echo "run test_ridership_scoring"
py -m tests.modules.bus_scoring.test_ridership_scoring

echo "run test_service_coverage_scoring"
py -m tests.modules.bus_scoring.test_service_coverage_scoring

echo "run test_travel_time_scoring"
py -m tests.modules.bus_scoring.test_travel_time_scoring