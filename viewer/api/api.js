const express = require("express");
const postgres = require("postgres");
const cors = require("cors");

const app = express();
const port = 3000;
app.use(cors({ origin: "*" }));

const sql = postgres({
  debug: (connection, query, params) => console.log(query),
});

app.get("/devices", async (req, res) => {
  res.json(await sql`select * from device;`);
});

app.get("/data", async (req, res) => {
  const minReceivedAt = new Date(
    req.query.minReceivedAt || "1900-01-01 00:00:00"
  );
  res.json(
    await sql`
      SELECT *
      FROM advertisement
      WHERE received_at >= ${minReceivedAt};`
  );
});

app.listen(port, () => {
  console.log(`API listening at http://localhost:${port}`);
});
