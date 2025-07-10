// routes/itemRoutes.js
import express from "express";
import Item from "../models/Item.js";

const router = express.Router();

router.get("/", async (req, res) => {
  try {
    console.log("Received request on /");
    const q = req.query.q || "";
    console.log(q)
    const items = await Item.find({ name: { $regex: q, $options: "i" } });

    res.status(200).json({
      success: true,
      message: items.length > 0 ? "Items fetched successfully." : "No items found.",
      data: items,
      count: items.length,
    });
  } catch (error) {
    console.error("Error fetching items:", error);
    res.status(500).json({
      success: false,
      message: "An error occurred while fetching items.",
      error: error.message,
    });
  }
});

router.post("/", async (req, res) => {
  const newItem = new Item(req.body);
  await newItem.save();
  res.status(201).json(newItem);
});

export default router;
