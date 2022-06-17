  const setLoading = (is_display) => {
    if (is_display) {
      document.getElementById("commit").classList.add("loading");
    } else {
      document.getElementById("commit").classList.remove("loading");
    }
  };

  const setMsgbox = (message, is_success) => {
    if (message) {
      document.getElementById("msgbox").style.display = "block";
      document.getElementById("status").innerHTML = message;
      document.getElementById('msgbox').classList.remove(is_success ? "toast-error" : "toast-success");
      document.getElementById('msgbox').classList.add(is_success ? "toast-success" : "toast-error");
    } else {
      document.getElementById("msgbox").style.display = "none";
      document.getElementById("status").innerHTML = "";
    }
  };

  const setSpec = (cpu, ram, storage) => {
    document.getElementById("cpu_cores").value = cpu;
    document.getElementById("ram_mb").value = ram;
    document.getElementById("storage_gb").value = storage;
  };

  const createMachine = () => {
    setLoading(true);

    const url = '/v1/machine';
    const params = ["name", "cpu_cores", "ram_mb", "storage_gb", "esxi_nodename", "comment"];
    const payloads = {};
    params.forEach(param => {
      payloads[param] = document.getElementById(param).value;
    });
    // console.log(payloads);

    fetch(url, {
      method: 'POST',
      body: JSON.stringify(payloads), // data can be `string` or {object}!
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(response => {
      if (!response.ok) {
        console.error("status code:", response.status);
        throw new Error(response.statusText);
      } 
      return response.json();
    })
    .then(data => {
      if (data === undefined) {
	return;
      }
      console.log('Success:', data);
      setMsgbox('Success: ' + data['message'], true);
      setLoading(false);
    })
    .catch(error => {
      console.error(error);
      setMsgbox("Failed: " + error, false);
      setLoading(false);
    });
  };

  const commitButton = document.getElementById('commit');
  commitButton.addEventListener("click", createMachine, false);

  const closeButton = document.getElementById('close');
  closeButton.addEventListener("click", () => {
    setMsgbox(false);
  }, false);

  document.getElementById('microButton').addEventListener("click", () => {
    setSpec(1, 512, 30);
  }, false);

  document.getElementById('smallButton').addEventListener("click", () => {
    setSpec(1, 1024, 30);
  }, false);

  document.getElementById('mediumButton').addEventListener("click", () => {
    setSpec(2, 2048, 50);
  }, false);

  document.getElementById('largeButton').addEventListener("click", () => {
    setSpec(4, 4096, 70);
  }, false);
