pid_error = 0
pid_output = 0

def control_temps(temp_set, measured_temp, previous_temp, error_integral, error_derivative, Kp, Ki, Kd):
    pid_error = temp_set - measured_temp # Calculate the error
    pid_output = Kp * pid_error + Ki * error_integral + Kd * error_derivative # Calculate the PID output
    error_integral += pid_error # Update the error integral
    error_derivative = pid_error - previous_temp # Update the error derivative
    previous_temp = measured_temp #previous temp is now the most recent temp (for next time)
        
    return pid_output, previous_temp, error_integral, error_derivative