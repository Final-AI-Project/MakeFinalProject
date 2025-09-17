import React, { useState, useMemo, useEffect } from "react"
import { useNavigate, Link } from "react-router-dom"
import { getUserInfo, logoutUser, updateUser } from "../api/member"
export default function EditProfile(){
    const [user, setUser] = useState(null)
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [message, setMessage] = useState('')
    const navigate = useNavigate()
    const token = useMemo(() => localStorage.getItem('token'))
    useEffect(() => {
        getUserInfo(token).then((res) => {
            setUser(res)
            setName(res.name)
    })
    .catch(() => setMessage('사용자 정보를 불러오지 못했습니다. :울다:'))
    }, [token])
    if (!user) return <div>로딩 중...</div>
    const handleUpdate = async () => {
        try {
            await updateUser({ name, password }, token)
            setMessage('회원정보가 수정되었습니다 :미소짓는_상기된_얼굴:')
            navigate('/mypage')
        } catch(e) {
            setMessage('수정 실패 :실망:')
        }
    }
    const handleLogout = async () => {
        await logoutUser(token);
        localStorage.removeItem('token')
        navigate('/login')
    }
    return (
        <div>
            <h2>회원정보 수정</h2>
            <p>아이디: {user.username}</p>
            <p>비밀번호: <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="새 비밀번호"/></p>
            <p>이름: <input value={name} onChange={(e) => setName(e.target.value)}/></p>
            <button onClick={handleUpdate}>수정하기</button>
            <button onClick={handleLogout}>로그아웃</button>
            <p>{message}</p>
            <p><Link to="/mypage">마이페이지</Link></p>
        </div>
    )
}