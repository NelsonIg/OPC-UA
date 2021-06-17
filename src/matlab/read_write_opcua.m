function [outputVal] = read_write_opcua(inputVal)
% - Connect to opcua server, if not connected
% - Read from opcua variable and return value
% - Write inputVal to opcua variable

% endpoint: opc.tcp://localhost:4840/server_example/

persistent uaClient; % opcua client
persistent initClient; % variable to track initialised clients
persistent rpm_node;
persistent inp_node;
persistent initNodes;

host = '192.168.0.183';
port = 4840;

% Connect to server if no client was initialised
if (isempty(initClient))
  
    try
        uaClient = opcua(host, port);
        connect(uaClient);
        initClient = 1; 
    catch exception
        warning('Connection to opcua client failed');
    end
% reconnect if connection lost
elseif uaClient.isConnected == 0
    connect(uaClient);
end




if isempty(uaClient) == 0
    % get nodes, if no nodes are already defined
    if uaClient.isConnected == 1 && (isempty(initNodes))
        rpm_node = opcuanode(2, 5);
        inp_node = opcuanode(2, 6);
        initNodes = 1;
    end


    % read from & read to server
    if uaClient.isConnected == 1 && (isempty(initNodes)) == 0
        writeValue(uaClient,inp_node, inputVal);
        % pause(0.100);
        [rpmVal, ~, ~] = readValue(uaClient, rpm_node);

    outputVal = double(rpmVal);

    end
end

