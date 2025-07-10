// models/Item.js
import mongoose from "mongoose";
const ItemSchema = new mongoose.Schema({
  name: String,
  category: String,
  description: String,
  price: Number,
});
export default mongoose.model("Item", ItemSchema);
