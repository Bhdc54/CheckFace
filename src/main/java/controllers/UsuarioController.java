package com.seuprojeto.controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import com.seuprojeto.models.Usuarios;
import com.seuprojeto.services.UsuariosService;

@RestController
@RequestMapping("/usuarios")
public class UsuarioController {

    @Autowired
    private UsuariosService usuariosService;

    @GetMapping
    public List<Usuarios> listar() {
        return usuariosService.listarTodos();
    }

    @PostMapping
    public Usuarios salvar(@RequestBody Usuarios usuario) {
        return usuariosService.salvar(usuario);
    }
}
