echo "run test_otp_scoring"
python -m tests.modules.bus_scoring.test_otp_scoring

echo "run test_ridership_scoring"
python -m tests.modules.bus_scoring.test_ridership_scoring

echo "run test_service_coverage_scoring"
python -m tests.modules.bus_scoring.test_service_coverage_scoring

echo "run test_travel_time_scoring"
python -m tests.modules.bus_scoring.test_travel_time_scoring

echo " RUN ALL SCORING"
python -m tests.compare_flow.test_compareflow