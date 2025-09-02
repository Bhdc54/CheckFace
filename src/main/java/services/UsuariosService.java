package com.seuprojeto.services;

import com.seuprojeto.models.Usuario;
import org.springframework.stereotype.Service;
import java.util.ArrayList;
import java.util.List;

@Service
public class UsuariosService {

    @Autowired
    private UsuariosRepository usuariosRepository;

    public List<Usuarios> listarTodos() {
        return usuariosRepository.findAll();
    }

    public Usuarios salvar(Usuarios usuario) {
        return usuariosRepository.save(usuario);
    }

    public Usuarios buscarPorId(Long id) {
        return usuariosRepository.findById(id).orElse(null);
    }
}