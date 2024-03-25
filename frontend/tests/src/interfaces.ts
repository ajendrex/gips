export interface PreguntaLikertNOAS {
    id: number
    texto: string
}

export interface Prueba {
    preguntalikertnoas_set: PreguntaLikertNOAS[]
}

export interface RespuestaParams {
    codigo: string
    idPregunta: number
    respuesta: string
}
