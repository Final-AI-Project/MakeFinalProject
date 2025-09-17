import React, { useEffect, useState } from 'react';
import { getUserInfo } from '../api/member';
import { Link } from 'react-router-dom';

export default function MyPage() {
	const [user, setUser] = useState(null);
	const [message, setMessage] = useState('');
	const token = localStorage.getItem('token');

	useEffect(() => {
		getUserInfo(token)
			.then((res) => setUser(res))
			.catch(() => setMessage(':x: 사용자 정보를 불러오지 못했습니다.'));
	}, [token]);

	if (!user) return <div>로딩 중...</div>;
	
	return (
		<div>
			<h2>마이페이지</h2>
			<p>아이디: {user.username}</p>
			<p>이름: {user.name}</p>
			<hr />
			<h3>메뉴</h3>
			<p><Link to="/board">📌 게시판</Link></p>
			<p><Link to="/chat">🗨 전체 채팅</Link></p>
			<p><Link to="/editprofile">💱 회원정보 수정</Link></p>
			<p>{message}</p>
		</div>
	);
}