package com.seuprojeto.models;

import jakarta.persistence.*;
import java.util.List;

@Entity
@Table(name = "usuarios")
public class Usuarios {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String nome;
    private String rga;
    private String siape;
    private String tipo; // aluno ou professor

    @ElementCollection
    @CollectionTable(name = "vetores_faciais", joinColumns = @JoinColumn(name = "usuario_id"))
    @Column(name = "valor")
    private List<Double> vetorFacial;

    // Getters e Setters
}
