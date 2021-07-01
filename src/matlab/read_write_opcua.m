function [outputVal] = read_write_opcua(inputVal)
% - Connect to opcua server, if not connected
% - Write inputVal to opcua variable% 
% - Read from opcua variable and return value


persistent uaClient; % opcua client
persistent initClient; % variable to track initialised clients
persistent rpmNode; % OPC UA Node for rpm of motor
persistent inpNode; % OPC UA Node for motor input [0-1]
persistent initNodes; % variable to track initialised Nodes

host = '192.168.0.183';
port = 4840;

% Connect to server if no client was initialised
if (isempty(initClient))
    uaClient = opcua(host, port);
    connect(uaClient);
    initClient = 1; 
% reconnect if connection lost
elseif uaClient.isConnected == 0
    connect(uaClient);
end




if isempty(uaClient) == 0
    % get nodes, if no nodes are already defined
    if uaClient.isConnected == 1 && (isempty(initNodes))
        rpmNode = opcuanode(2, 5);
        inpNode = opcuanode(2, 6);
        initNodes = 1;
    end


    % read from & read to server
    if uaClient.isConnected == 1 && (isempty(initNodes)) == 0
        writeValue(uaClient,inpNode, inputVal);
        % pause(0.100); % time for the motor to react --> not needed
        [rpmVal, ~, ~] = readValue(uaClient, rpmNode);

    outputVal = double(rpmVal);

    end
end

