// Render the OpenCode Zen model list into the "Supported models" table.
// Data source: models.json (generated from the Zen API by
// .github/workflows/models.yml). Mirrors the family/status logic used by the
// integration itself (custom_components/opencode/const.py).
(function () {
  "use strict";

  var tableBody = document.getElementById("models-body");
  var fetchInfo = document.getElementById("models-fetch-info");

  function esc(s) {
    var div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function modelChips(models) {
    return models
      .map(function (m) {
        var title = m.free ? "free" : "";
        var tag = m.free ? ' class="chip chip-free"' : ' class="chip"';
        return (
          "<code" + tag + (title ? ' title="' + title + '"' : "") + ">" +
          esc(m.id) +
          "</code>"
        );
      })
      .join("");
  }

  function render(data) {
    var groups = {};
    data.models.forEach(function (m) {
      (groups[m.family] = groups[m.family] || []).push(m);
    });

    var order = Object.keys(groups).sort(function (a, b) {
      return a.localeCompare(b);
    });

    var rows = order.map(function (family) {
      var models = groups[family].sort(function (a, b) {
        return a.id.localeCompare(b.id);
      });
      return (
        "<tr><td>" + esc(family) + "</td><td>" + modelChips(models) + "</td></tr>"
      );
    });

    tableBody.innerHTML = rows.join("");

    var fetched = new Date(data.fetched_at);
    fetchInfo.textContent =
      data.count + " models · refreshed " + fetched.toUTCString() +
      " · source: " + data.source;
  }

  function renderError(err) {
    tableBody.innerHTML =
      '<tr><td colspan="2">Could not load the model list. ' +
      "OpenCode Zen models are documented at " +
      '<a href="https://opencode.ai/docs/zen/" target="_blank" rel="noopener">' +
      "opencode.ai/docs/zen</a>.</td></tr>";
    if (fetchInfo) {
      fetchInfo.textContent = "models.json unavailable: " + String(err);
    }
  }

  fetch("models.json", { cache: "no-cache" })
    .then(function (resp) {
      if (!resp.ok) {
        throw new Error("HTTP " + resp.status);
      }
      return resp.json();
    })
    .then(render)
    .catch(renderError);
})();
