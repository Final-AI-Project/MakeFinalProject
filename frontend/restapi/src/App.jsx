import React from 'react';
import { Routes, Route, Navigate} from 'react-router-dom'
import Login from "./pages/Login"
import Register from './pages/Register'
import Mypage from './pages/mypage'
import EditProfile from './pages/EditProfile'
import BoardWrite from './pages/BoardWrite'
import Board from './pages/BoardList'

export default function App() {
	return (
		<Routes>
			<Route path="/" element={<Navigate to="/login"/>}/>
			<Route path="/login" element={<Login/>}/>
			<Route path="/register" element={<Register/>}/>
			<Route path="/Mypage" element={<Mypage/>}/>
			<Route path="/editprofile" element={<EditProfile/>}/>
			<Route path="/board/write" element={<BoardWrite/>}/>
			<Route path="/board" element={<Board/>}/>
		</Routes>
	)
}