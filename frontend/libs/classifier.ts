// libs/classifier.ts
export type ClassifyResult = { species: string; confidence: number };

const SERVER_IP = process.env.EXPO_PUBLIC_SERVER_IP || "http://192.168.9.4";
export const CLASSIFIER_URL = `${SERVER_IP}:4000/plants/classify-species`;

export async function classifyImage(uri: string): Promise<ClassifyResult> {
	const form = new FormData();
	form.append("image", { uri, name: "photo.jpg", type: "image/jpeg" } as any);

	const res = await fetch(CLASSIFIER_URL, { method: "POST", body: form });
	if (!res.ok) throw new Error(`HTTP ${res.status}`);

	const data = await res.json();

	// 표준 응답
	if (data?.success && data.species) {
		const conf = Number(data.confidence ?? 0);
		return { species: String(data.species), confidence: Math.round(conf <= 1 ? conf * 100 : conf) };
	}
	// 유연 파싱
	const sp = data?.label ?? data?.top?.[0]?.label ?? data?.top?.[0]?.[0] ?? "알수없음";
	const cf = data?.prob ?? data?.confidence ?? data?.top?.[0]?.prob ?? data?.top?.[0]?.[1] ?? 0;
	const conf = Number(cf);
	return { species: String(sp), confidence: Math.round(conf <= 1 ? conf * 100 : conf) };
}
