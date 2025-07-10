// server.js
import express from "express";
import mongoose from "mongoose";
import cors from "cors";
import dotenv from "dotenv";
import ItemRoutes from "./routes/itemRoutes.js";

dotenv.config();
const app = express();
app.use(cors());
app.use(express.json());

mongoose.connect(process.env.MONGO_URI).then(() => {
  console.log("Mongo Connected");
  app.listen(5000, () => console.log("Server running on 5000"));
});

app.use("/items", ItemRoutes);
