function [inpMotor] = motor_control(currentRPM, desiredRPM, stepSize, min, max)
    persistent inp;
    
    if isempty(inp)
        inp = min;
    end
    
    if currentRPM < desiredRPM
        if inp < max
            inp = inp + stepSize;
        end
    elseif currentRPM > desiredRPM
        if inp > min
            inp = inp - stepSize;
        end
    end
    
    
inpMotor = inp;
end

