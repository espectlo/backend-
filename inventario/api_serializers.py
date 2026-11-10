from rest_framework import serializers

from .models import Herramienta, Insumo, Solicitud


class InsumoSerializer(serializers.ModelSerializer):
    estado = serializers.CharField(read_only=True)

    class Meta:
        model = Insumo
        fields = ('id', 'nombre', 'cantidad', 'stock_minimo', 'estado')


class HerramientaSerializer(serializers.ModelSerializer):
    puede_usarse = serializers.BooleanField(read_only=True)

    class Meta:
        model = Herramienta
        fields = ('id', 'nombre', 'estado', 'tratamiento', 'puede_usarse')


class SolicitudSerializer(serializers.ModelSerializer):
    usuario = serializers.IntegerField(source='usuario_id', read_only=True)
    usuario_nombre = serializers.CharField(read_only=True)
    insumo_nombre = serializers.CharField(read_only=True)
    creado = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Solicitud
        fields = (
            'id',
            'usuario',
            'usuario_nombre',
            'insumo',
            'insumo_nombre',
            'cantidad_solicitada',
            'creado',
            'estado',
            'justificacion',
        )
        read_only_fields = ('estado', 'justificacion')

    def create(self, validated_data):
        user = self.context['request'].user
        insumo = validated_data['insumo']
        return Solicitud.objects.create(
            usuario=user,
            usuario_nombre=user.get_username(),
            insumo=insumo,
            insumo_nombre=insumo.nombre,
            cantidad_solicitada=validated_data['cantidad_solicitada'],
        )


class SolicitudDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solicitud
        fields = ('estado', 'justificacion')

    def validate(self, attrs):
        solicitud = self.instance
        if solicitud.estado != Solicitud.Estado.PENDIENTE:
            raise serializers.ValidationError({
                'estado': 'La solicitud ya fue resuelta.'
            })

        estado = attrs.get('estado')
        if estado not in (Solicitud.Estado.APROBADA, Solicitud.Estado.RECHAZADA):
            raise serializers.ValidationError({
                'estado': 'Selecciona Aprobado o Rechazado para resolver la solicitud.'
            })

        justificacion = attrs.get('justificacion', '').strip()
        if not justificacion:
            raise serializers.ValidationError({
                'justificacion': 'Es obligatoria para resolver la solicitud.'
            })
        attrs['justificacion'] = justificacion
        return attrs
