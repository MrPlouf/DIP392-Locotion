import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Bell, CheckCircle, Clock } from "lucide-react";

const billsData = [
  { id: 1, name: "Electricity Bill", amount: "$50", dueDate: "2025-04-01", status: "Due" },
  { id: 2, name: "Internet Bill", amount: "$30", dueDate: "2025-03-28", status: "Paid" },
  { id: 3, name: "Water Bill", amount: "$20", dueDate: "2025-03-30", status: "Upcoming" },
];

export default function Dashboard() {
  const [bills, setBills] = useState(billsData);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">House Bill Management</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {bills.map((bill) => (
          <Card key={bill.id} className="p-4 border rounded-lg shadow-md">
            <CardContent>
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-semibold">{bill.name}</h2>
                  <p className="text-sm text-gray-500">Due: {bill.dueDate}</p>
                  <p className="font-bold">{bill.amount}</p>
                </div>
                <div>
                  {bill.status === "Paid" && <CheckCircle className="text-green-500" />}
                  {bill.status === "Due" && <Clock className="text-red-500" />}
                  {bill.status === "Upcoming" && <Bell className="text-yellow-500" />}
                </div>
              </div>
              {bill.status !== "Paid" && (
                <Button className="mt-3 w-full">Pay Now</Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
