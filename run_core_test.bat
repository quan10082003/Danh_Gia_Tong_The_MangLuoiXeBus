echo "run test_vehicle_processor"
py -m tests.modules.core_data_processor.test_vehicle_processor

echo "run test_schedule_processor"
py -m tests.modules.core_data_processor.test_schedule_processor

echo "run test_plan_input_processor"
py -m tests.modules.core_data_processor.test_plan_input_processor

echo "run test_network_processor"
py -m tests.modules.core_data_processor.test_network_processor