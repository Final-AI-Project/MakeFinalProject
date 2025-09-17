import React, { useState } from "react"
import { registerUser } from "../api/member"
import { useNavigate, Link } from "react-router-dom"

export default function Register() {
	const [username, setUsername] = useState('')
	const [password, setPassword] = useState('')
	const [name, setName] = useState('')
	const [message, setMessage] = useState('')
    const navigate = useNavigate()

	const handleResister = async () => {
		try {
			await registerUser({username, password, name});
			setMessage('회원가입 성공');
			navigate('/login');
		} catch (e) {
			setMessage('회원가입 실패')
		}
	}

	return (
		<div>
			<h2>회원가입</h2>
			<p>아이디 <input type="text" value={username} onChange={(e) => setUsername(e.target.value)}/></p>
			<p>비밀번호 <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}/> </p>
			<p>이름 <input type="text" value={name} onChange={(e) => setName(e.target.value)}/> </p>
			<button onClick={handleResister} type="submit">회원가입</button>
			<p>{message}</p>
			<p>로그인 페이지 이동? <Link to="/Login">로그인</Link></p>
		</div>
	)
}