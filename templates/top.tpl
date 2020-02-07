{% include "header.tpl" %}
  <h1>VM Manager</h1>
  <table border=1>
    <thead>
      <tr>
        <th>Power</th>
        <th>Physical Host</th>
        <th>ID</th>
        <th>Name</th>
        <th>Datastore</th>
        <th>Datastore Path</th>
        <th>Guest OS</th>
        <th>VM Version</th>
        <th>Comment</th>
      </tr>
    </thead>
    <tbody>
    {% for machine in machines %}
      <tr>
        {% if machine.power == 'on' %}
        <td>● ON</td>
        {% elif machine.power == 'off' %}
        <td>◯ OFF</td>
        {% else %}
        <td>{{ machine.power }}</td>
        {% endif %}
        <td>{{ machine.physical_host }}</td>
        <td>{{ machine.id }}</td>
        <td>{{ machine.name }}</td>
        <td>{{ machine.datastore }}</td>
        <td>{{ machine.datastore_path }}</td>
        <td>{{ machine.guest_os }}</td>
        <td>{{ machine.vm_version }}</td>
        <td>{{ machine.comment }}</td>
      </tr>
    {% endfor %}
    </tbody>
  <table>
{% include "footer.tpl" %}
