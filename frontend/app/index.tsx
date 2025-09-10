// app/index.tsx
import React, { useEffect, useState } from "react";
import { ActivityIndicator, View } from "react-native";
import { Redirect } from "expo-router";
import { getToken } from "../lib/auth";

export default function Index() {
    return <Redirect href="/(public)/splash" />;
}