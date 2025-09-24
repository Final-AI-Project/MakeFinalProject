import React from "react";
import { View, Text, StyleSheet } from "react-native";
import {
  getPlantHumidityRange,
  getHumidityStatus,
  getHumidityStatusColor,
  PlantHumidityRange,
} from "../../utils/plantHumidityRanges";

interface HumidityGaugeProps {
  currentHumidity: number;
  species?: string;
  size?: "small" | "medium" | "large";
  showRange?: boolean;
  showStatus?: boolean;
}

export default function HumidityGauge({
  currentHumidity,
  species,
  size = "medium",
  showRange = true,
  showStatus = true,
}: HumidityGaugeProps) {
  const range = getPlantHumidityRange(species);
  const status = getHumidityStatus(currentHumidity, range);
  const statusColor = getHumidityStatusColor(status);

  const sizeStyles = {
    small: {
      container: styles.smallContainer,
      gauge: styles.smallGauge,
      text: styles.smallText,
      rangeText: styles.smallRangeText,
    },
    medium: {
      container: styles.mediumContainer,
      gauge: styles.mediumGauge,
      text: styles.mediumText,
      rangeText: styles.mediumRangeText,
    },
    large: {
      container: styles.largeContainer,
      gauge: styles.largeGauge,
      text: styles.largeText,
      rangeText: styles.largeRangeText,
    },
  };

  const currentStyles = sizeStyles[size];

  return (
    <View style={[styles.container, currentStyles.container]}>
      {/* 현재 습도 표시 */}
      <View
        style={[
          styles.gauge,
          currentStyles.gauge,
          { borderColor: statusColor },
        ]}
      >
        <Text
          style={[
            styles.humidityText,
            currentStyles.text,
            { color: statusColor },
          ]}
        >
          {currentHumidity.toFixed(0)}%
        </Text>
      </View>

      {/* 최적 습도 범위 표시 */}
      {showRange && (
        <View style={styles.rangeContainer}>
          <View style={styles.rangeBar}>
            <View style={styles.rangeTrack}>
              {/* 최적 범위 표시 */}
              <View
                style={[
                  styles.optimalRange,
                  {
                    left: `${range.min}%`,
                    width: `${range.max - range.min}%`,
                  },
                ]}
              />
              {/* 현재 습도 위치 표시 */}
              <View
                style={[
                  styles.currentIndicator,
                  {
                    left: `${Math.min(100, Math.max(0, currentHumidity))}%`,
                    backgroundColor: statusColor,
                  },
                ]}
              />
            </View>
          </View>
          <Text style={[styles.rangeText, currentStyles.rangeText]}>
            최적: {range.min}-{range.max}%
          </Text>
        </View>
      )}

      {/* 습도 상태 표시 */}
      {showStatus && (
        <View style={styles.statusContainer}>
          <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
          <Text style={[styles.statusText, currentStyles.rangeText]}>
            {status === "optimal" && "적정"}
            {status === "low" && "부족"}
            {status === "high" && "과다"}
            {status === "critical" && "위험"}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
  },
  gauge: {
    borderWidth: 3,
    borderRadius: 50,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255, 255, 255, 0.1)",
  },
  humidityText: {
    fontWeight: "bold",
  },
  rangeContainer: {
    marginTop: 8,
    width: "100%",
    alignItems: "center",
  },
  rangeBar: {
    width: "100%",
    height: 20,
    position: "relative",
  },
  rangeTrack: {
    width: "100%",
    height: 6,
    backgroundColor: "#E0E0E0",
    borderRadius: 3,
    position: "relative",
    marginTop: 7,
  },
  optimalRange: {
    position: "absolute",
    height: "100%",
    backgroundColor: "#4CAF50",
    borderRadius: 3,
    opacity: 0.3,
  },
  currentIndicator: {
    position: "absolute",
    width: 12,
    height: 12,
    borderRadius: 6,
    top: -3,
    marginLeft: -6,
    borderWidth: 2,
    borderColor: "#fff",
  },
  rangeText: {
    marginTop: 4,
    textAlign: "center",
  },
  statusContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 4,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 4,
  },
  statusText: {
    fontWeight: "500",
  },

  // 크기별 스타일
  smallContainer: {
    minWidth: 60,
  },
  smallGauge: {
    width: 50,
    height: 50,
  },
  smallText: {
    fontSize: 12,
  },
  smallRangeText: {
    fontSize: 10,
  },

  mediumContainer: {
    minWidth: 80,
  },
  mediumGauge: {
    width: 70,
    height: 70,
  },
  mediumText: {
    fontSize: 16,
  },
  mediumRangeText: {
    fontSize: 12,
  },

  largeContainer: {
    minWidth: 100,
  },
  largeGauge: {
    width: 90,
    height: 90,
  },
  largeText: {
    fontSize: 20,
  },
  largeRangeText: {
    fontSize: 14,
  },
});
