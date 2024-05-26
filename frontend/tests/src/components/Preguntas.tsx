import {PreguntaLikertNOAS, RespuestaParams} from "../interfaces"
import React, {useCallback, useEffect, useRef, useState} from "react"
import {useMutation} from "react-query"
import {
    Alert,
    AlertDescription,
    AlertIcon,
    Box,
    Button,
    Card,
    FormControl,
    FormLabel,
    Heading,
    Radio,
    RadioGroup, Spinner,
    Stack,
    Switch,
    Text
} from "@chakra-ui/react"
import axios from "axios"
import {getCsrfToken} from "../csrf"

const submitRespuesta = async ({codigo, idPregunta, respuesta}: RespuestaParams): Promise<void> => {
    try {
        await axios.post(
            `/api/tests/respuestas-likert-noas/?codigo=${codigo}`,
            {
                pregunta: idPregunta,
                alternativa: respuesta,
            },
            {
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                }
            }
        )
    } catch (error: any) {
        const errorMsg = error.response.data[0] || error.response.data.detail || "Algo salió mal"
        throw new Error(errorMsg)
    }
}

const findNextQuestion = (
        preguntas: PreguntaLikertNOAS[],
        respuestas: { [preguntaId: number]: string },
        currentId: number,
    ): number => {
    let pastCurrent = false
    let index = 0
    let firstUnanswered = -1
    let nextUnanswered = -1

    for (const pregunta of preguntas) {
        if (!respuestas[pregunta.id]) {
            if (firstUnanswered === -1) {
                firstUnanswered = index
            }
            if (pastCurrent) {
                nextUnanswered = index
                break
            }
        }
        if (pregunta.id === currentId) {
            pastCurrent = true
        }

        index++
    }

    return nextUnanswered !== -1 ? nextUnanswered : firstUnanswered
}

interface PreguntasProps {
    preguntas: PreguntaLikertNOAS[]
    codigo: string
    successCallback: () => void
}

export const Preguntas = ({preguntas, codigo, successCallback}: PreguntasProps) => {
    const [autoScroll, setAutoScroll] = useState(true)
    const [respuestas, setRespuestas] = useState<{ [preguntaId: number]: string }>({})
    const preguntaRefs = useRef<(HTMLDivElement | null)[]>([])
    const [preguntaEnFoco, setPreguntaEnFoco] = useState<number | null>(null)
    const [preguntaRespondida, setPreguntaRespondida] = useState<number | null>(null)
    const [respuestasPendientes, setRespuestasPendientes] = useState<number[]>([])
    const [respuestasConError, setRespuestasConError] = useState<number[]>([])
    const [reintentando, setReintentando] = useState(0)

    const mutation = useMutation(
        ({codigo, idPregunta, respuesta}: RespuestaParams) => submitRespuesta({
            codigo,
            idPregunta,
            respuesta
        }),
        {
            onSuccess: (data, variables) => {
                setRespuestasPendientes(respuestasPendientes.filter(id => id !== variables.idPregunta))
                setRespuestasConError(respuestasConError.filter(id => id !== variables.idPregunta))
            },
            onError: (error, variables) => {
                setRespuestasConError([...respuestasConError, variables.idPregunta])
                setRespuestasPendientes(respuestasPendientes.filter(id => id !== variables.idPregunta))
            },
            retry: 3,
            retryDelay: 1000,
        }
    )

    const reintentarGuardarRespuestas = () => {
        const respuestasAReintentar = Array.from(new Set(respuestasConError))
        for (const idPregunta of respuestasAReintentar) {
            setReintentando(r => r + 1)
            setRespuestasPendientes([...respuestasPendientes, idPregunta])
            mutation.mutate(
                {codigo, idPregunta, respuesta: respuestas[idPregunta]},
                {
                    onSettled: () => {
                        setReintentando(r => r - 1)
                    }
                }
            )
        }
    }

    useEffect(() => {
        if (preguntaRefs.current[0]) {
            setPreguntaEnFoco(preguntas[0].id)
        }
    }, [preguntas, preguntaRefs])

    const observarScroll = () => {
        const alturaTotalDocumento = document.documentElement.scrollHeight
        const alturaViewport = window.innerHeight
        const maxScrollY = alturaTotalDocumento - alturaViewport
        const alturaPorPregunta = maxScrollY / (preguntas.length || 1)
        // Calcula el índice de la pregunta basado en el scroll actual
        const indicePreguntaEnFoco = Math.floor(window.scrollY / alturaPorPregunta)

        console.debug(`h_total: ${alturaTotalDocumento}, viewPort: ${alturaViewport}, alturaPorPregunta: ${alturaPorPregunta}, maxScrolY: ${maxScrollY} scrollY: ${window.scrollY}, indicePregunta: ${indicePreguntaEnFoco}`)

        // Asegura que el índice está dentro de los límites del array de preguntas
        if (indicePreguntaEnFoco >= 0 && indicePreguntaEnFoco < (preguntas.length || 0)) {
            const preguntaId = preguntas[indicePreguntaEnFoco].id
            setPreguntaEnFoco(preguntaId || null)
        }
    }

    useEffect(() => {
        window.addEventListener('scroll', observarScroll)

        return () => {
            window.removeEventListener('scroll', observarScroll)
        }
    }, [preguntas, observarScroll])

    const handleAnswerSelect = (idPregunta: number, respuesta: string) => {
        const nuevasRespuestas = {...respuestas, [idPregunta]: respuesta}
        setPreguntaRespondida(idPregunta)
        setRespuestas(nuevasRespuestas)

        setRespuestasPendientes([...respuestasPendientes, idPregunta])
        mutation.mutate({codigo, idPregunta, respuesta})
    }

    const enfocarPregunta = useCallback((index: number) => {
        const alturaTotalDocumento = document.documentElement.scrollHeight
        const alturaViewport = window.innerHeight
        const maxScrollY = alturaTotalDocumento - alturaViewport

        if (index === -1) {
            window.scrollTo({top: maxScrollY, behavior: 'smooth'})
        } else if (autoScroll) {
            const alturaPorPregunta = maxScrollY / (preguntas.length || 1)

            // Calcula el nuevo scrollY basado en el índice de la pregunta
            const nuevoScrollY = alturaPorPregunta * index + alturaPorPregunta / 2

            // Mueve el scroll a la posición calculada
            window.scrollTo({top: nuevoScrollY, behavior: 'smooth'})
        } else if (index < preguntaRefs.current.length) {
            setPreguntaEnFoco(preguntas[index].id)
        }
    },
        [preguntas, autoScroll])

    useEffect(() => {
        if (autoScroll && preguntaRespondida !== null) {
            const siguientePreguntaIndex = findNextQuestion(preguntas, respuestas, preguntaRespondida);
            enfocarPregunta(siguientePreguntaIndex);
        }
    }, [respuestas, autoScroll, preguntaRespondida, preguntas, enfocarPregunta]);

    return (
        <>
            <Box position="fixed" bottom="20px" right="20px" zIndex="1000">
                <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="auto-scroll" mb="0" mr="2">
                        Auto-scroll
                    </FormLabel>
                    <Switch id="auto-scroll" isChecked={autoScroll} onChange={() => setAutoScroll(!autoScroll)} />
                </FormControl>
            </Box>
            <Box h={30} />
            {
                preguntas.map((pregunta, index) => (
                    <Box
                        key={pregunta.id}
                        ref={el => preguntaRefs.current[index] = el}
                        padding="20px"
                        mb="4"
                        boxShadow="lg"
                        borderRadius="md"
                        opacity={preguntaEnFoco === pregunta.id ? 1 : 0.5}
                        onClick={() => enfocarPregunta(index)}
                    >
                        <Box
                            h={150}
                            display="flex"
                            flexDirection="column"
                            justifyContent="center"
                        >
                            <Text
                                align="center"
                                fontWeight="bold"
                                fontFamily="'Roboto Slab', serif"
                                opacity={preguntaEnFoco === pregunta.id ? 1 : 0.5}
                            >{pregunta.texto}</Text>
                        </Box>
                        <Box
                            display="flex"
                            flexDirection="row"
                            alignItems="center"
                            justifyContent="space-between"
                        >
                            <RadioGroup
                                onChange={(value) => handleAnswerSelect(pregunta.id, value)}
                                value={respuestas[pregunta.id]}
                            >
                                <Stack direction="column">
                                    {[
                                        {text: "Rara vez o nunca", code: "N"},
                                        {text: "Ocasionalmente", code: "O"},
                                        {text: "A menudo", code: "A"},
                                        {text: "Siempre o casi siempre", code: "S"},
                                    ].map(({text, code}) => (
                                        <Radio
                                            key={code}
                                            value={code}
                                            opacity={preguntaEnFoco === pregunta.id ? 1 : 0.5}
                                            isDisabled={respuestasPendientes.includes(pregunta.id)}
                                        >
                                            {text}
                                        </Radio>
                                    ))}
                                </Stack>
                            </RadioGroup>
                            {!reintentando && respuestasPendientes.includes(pregunta.id) ? (
                                <Spinner />
                            ) : null}
                        </Box>
                    </Box>
                ))
            }
            <Box h={300}>
                {
                    Object.keys(respuestas).length === preguntas.length ? (
                        respuestasConError.length || reintentando ? (
                            <Stack spacing="30px" align="center">
                                <Alert status="error">
                                    <AlertIcon />
                                    <AlertDescription>
                                        Hubo problemas guardando algunas respuestas. Asegúrate de tener internet y luego
                                        pincha el botón reintentar.
                                    </AlertDescription>
                                </Alert>
                                { reintentando ? (
                                    <Spinner />
                                ) : (
                                    <Button
                                        width="50%"
                                        onClick={reintentarGuardarRespuestas}
                                        variant="solid"
                                        colorScheme="green"
                                    >
                                        Reintentar
                                    </Button>
                                )}
                            </Stack>
                        ) : respuestasPendientes.length ? null : (
                            <Card p="10px">
                                <Box
                                    display="flex"
                                    justifyContent="center"
                                    alignItems="center"
                                    flexDirection="column"
                                >
                                    <Stack spacing="30px">
                                        <Heading size="sm" mb="10px" mt="50px" textAlign="center">
                                            ¡Perfecto!<br />
                                        </Heading>
                                        <Text lineHeight="25px">
                                            Ahora debes agendar una entrevista con el psicólogo en el siguiente paso.
                                        </Text>
                                        <Box display="flex" justifyContent="center" mb="10px">
                                            <Button
                                                colorScheme="teal"
                                                onClick={successCallback}
                                            >
                                                Agendar Llamada
                                            </Button>
                                        </Box>
                                    </Stack>
                                </Box>
                            </Card>
                    )) : null
                }
            </Box>
        </>
    )
}
