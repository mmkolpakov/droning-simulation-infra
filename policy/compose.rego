package compose

import rego.v1

deny contains message if {
	some name, service in input.services
	service.privileged == true
	message := sprintf("service %q enables privileged mode", [name])
}

deny contains message if {
	some name, service in input.services
	service.network_mode == "host"
	message := sprintf("service %q joins the host network namespace", [name])
}

deny contains message if {
	some name, service in input.services
	service.ipc == "host"
	message := sprintf("service %q joins the host IPC namespace", [name])
}

deny contains message if {
	some name, service in input.services
	service.pid == "host"
	message := sprintf("service %q joins the host PID namespace", [name])
}

deny contains message if {
	some name, service in input.services
	count(object.get(service, "cap_add", [])) > 0
	message := sprintf("service %q adds Linux capabilities", [name])
}

deny contains message if {
	some name, service in input.services
	not "ALL" in object.get(service, "cap_drop", [])
	message := sprintf("service %q does not drop all Linux capabilities", [name])
}

deny contains message if {
	some name, service in input.services
	not "no-new-privileges:true" in object.get(service, "security_opt", [])
	message := sprintf("service %q does not enable no-new-privileges", [name])
}

deny contains message if {
	some name, service in input.services
	some volume in object.get(service, "volumes", [])
	source := volume_source(volume)
	docker_socket(source)
	message := sprintf("service %q mounts the Docker control socket", [name])
}

deny contains message if {
	some name, service in input.services
	some device in object.get(service, "devices", [])
	broad_device(device)
	message := sprintf("service %q exposes a broad device mapping", [name])
}

deny contains message if {
	some name, service in input.services
	some device in object.get(service, "devices", [])
	unstable_serial_device(device_source(device))
	message := sprintf("service %q exposes an unstable serial device path", [name])
}

deny contains message if {
	service := input.services["serial-device-preflight"]
	some device in object.get(service, "devices", [])
	not stable_serial_device(device_source(device))
	message := "service \"serial-device-preflight\" requires /dev/serial/by-id or /dev/robotics"
}

deny contains message if {
	some name, service in input.services
	"can-observation" in object.get(service, "profiles", [])
	count(object.get(service, "devices", [])) > 0
	message := sprintf("service %q exposes a device in the CAN observation profile", [name])
}

deny contains message if {
	some name, service in input.services
	"can-observation" in object.get(service, "profiles", [])
	count(object.get(service, "ports", [])) > 0
	message := sprintf("service %q publishes a port in the CAN observation profile", [name])
}

deny contains message if {
	some name, service in input.services
	"can-observation" in object.get(service, "profiles", [])
	not "robotics-can-observation" in object.keys(object.get(service, "networks", {}))
	message := sprintf("service %q is outside the dedicated CAN observation network", [name])
}

deny contains message if {
	some name, service in input.services
	"can-observation" in object.get(service, "profiles", [])
	some token in command_tokens(service)
	forbidden_can_command(token)
	message := sprintf("service %q contains CAN transmit or bidirectional tooling", [name])
}

volume_source(volume) := source if {
	is_object(volume)
	source := object.get(volume, "source", "")
}

volume_source(volume) := source if {
	is_string(volume)
	source := split(volume, ":")[0]
}

docker_socket(source) if {
	source == "/var/run/docker.sock"
}

docker_socket(source) if {
	source == "/run/docker.sock"
}

broad_device(device) if {
	is_string(device)
	startswith(device, "/dev:/dev")
}

broad_device(device) if {
	is_object(device)
	object.get(device, "source", "") == "/dev"
}

device_source(device) := source if {
	is_object(device)
	source := object.get(device, "source", "")
}

device_source(device) := source if {
	is_string(device)
	source := split(device, ":")[0]
}

unstable_serial_device(source) if {
	startswith(source, "/dev/ttyUSB")
}

unstable_serial_device(source) if {
	startswith(source, "/dev/ttyACM")
}

unstable_serial_device(source) if {
	contains(source, "*")
}

stable_serial_device(source) if {
	startswith(source, "/dev/serial/by-id/")
}

stable_serial_device(source) if {
	startswith(source, "/dev/robotics/")
}

command_tokens(service) := command if {
	command := object.get(service, "command", [])
	is_array(command)
}

command_tokens(service) := tokens if {
	command := object.get(service, "command", "")
	is_string(command)
	tokens := split(command, " ")
}

forbidden_can_command(token) if {
	regex.match(
		"(^|.*/|.*[[:space:]])(cannelloni|cansend|socketcand)([[:space:]].*|$)",
		lower(token),
	)
}
