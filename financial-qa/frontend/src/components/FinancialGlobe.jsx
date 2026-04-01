import { useRef, useEffect } from 'react'
import { useFrame }          from '@react-three/fiber'
import { useGLTF, useAnimations, Html, OrbitControls } from '@react-three/drei'
import * as THREE from 'three'

/* Preload so the model is ready before the Canvas renders */
useGLTF.preload('/hologram_planet_earth_animated.glb')

/* ── Floating question chip ── */
function QuestionChip({ text, position, onClick }) {
  return (
    <Html position={position} distanceFactor={5} center>
      <button
        onClick={onClick}
        style={{
          background: 'rgba(8, 18, 38, 0.88)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(100, 180, 255, 0.35)',
          borderLeft: '3px solid rgba(80, 160, 240, 0.85)',
          borderRadius: '0 8px 8px 0',
          padding: '7px 16px',
          cursor: 'pointer',
          color: '#c8e4f8',
          fontSize: 13,
          fontFamily: 'inherit',
          whiteSpace: 'nowrap',
          letterSpacing: '0.02em',
          boxShadow: '0 0 16px rgba(40,120,200,0.2)',
          transition: 'all 0.2s',
        }}
        onMouseEnter={e => {
          e.currentTarget.style.borderLeftColor = '#80c4ff'
          e.currentTarget.style.boxShadow = '0 0 28px rgba(60,160,240,0.5)'
          e.currentTarget.style.background = 'rgba(12,30,60,0.96)'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.borderLeftColor = 'rgba(80,160,240,0.85)'
          e.currentTarget.style.boxShadow = '0 0 16px rgba(40,120,200,0.2)'
          e.currentTarget.style.background = 'rgba(8,18,38,0.88)'
        }}
      >
        {text}
      </button>
    </Html>
  )
}

/* ── Earth model ── */
function EarthModel() {
  const groupRef = useRef()
  const { scene, animations } = useGLTF('/hologram_planet_earth_animated.glb')
  const { actions, names }    = useAnimations(animations, groupRef)

  /* Play all embedded animations on mount */
  useEffect(() => {
    names.forEach(name => {
      const action = actions[name]
      if (action) {
        action.reset().play()
        action.timeScale = 1
      }
    })
  }, [actions, names])

  /* Normalise scale: fit the model into a ~3-unit bounding sphere */
  useEffect(() => {
    if (!scene) return
    const box    = new THREE.Box3().setFromObject(scene)
    const size   = box.getSize(new THREE.Vector3())
    const maxDim = Math.max(size.x, size.y, size.z)
    const scale  = 3.0 / maxDim          // target diameter ≈ 3 units
    scene.scale.setScalar(scale)
    // Centre the model at origin
    box.setFromObject(scene)
    const centre = box.getCenter(new THREE.Vector3())
    scene.position.sub(centre)
  }, [scene])

  return (
    <group ref={groupRef}>
      <primitive object={scene} />
    </group>
  )
}

/* ── Main scene ── */
export default function FinancialGlobe({ onQuestionClick, showQuestions = true }) {
  const QUESTIONS = [
    { text: 'Analyze TSLA margins',           position: [ 2.8,  1.2,  0.6] },
    { text: 'What is a P/E ratio?',           position: [-2.7,  0.3,  0.8] },
    { text: 'NVDA 30-day performance',        position: [-2.2,  1.6, -1.4] },
    { text: 'Explain dollar cost averaging',  position: [ 2.4, -0.4, -0.9] },
  ]

  return (
    <>
      {/* Neutral ambient so the model's own materials show correctly */}
      <ambientLight intensity={0.6} />
      <directionalLight position={[4, 3, 5]}  intensity={0.8} color="#d0e8ff" />
      <directionalLight position={[-4, -2, -3]} intensity={0.3} color="#1a4888" />

      <EarthModel />

      {showQuestions && QUESTIONS.map(q => (
        <QuestionChip
          key={q.text}
          text={q.text}
          position={q.position}
          onClick={() => onQuestionClick?.(q.text)}
        />
      ))}

      <OrbitControls
        autoRotate
        autoRotateSpeed={0.5}
        enableZoom={false}
        enablePan={false}
        minPolarAngle={Math.PI * 0.2}
        maxPolarAngle={Math.PI * 0.8}
      />
    </>
  )
}
