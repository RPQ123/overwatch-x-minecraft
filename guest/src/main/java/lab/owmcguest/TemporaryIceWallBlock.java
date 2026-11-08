package lab.owmcguest;
import com.mojang.serialization.MapCodec;
import net.minecraft.block.*;
import net.minecraft.state.StateManager;
import net.minecraft.state.property.IntProperty;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.BlockView;

/** Invisible temporary collision; client renders the same plan as ice. A
 * fractional top avoids floating above slabs/stairs after the wall rises. */
public final class TemporaryIceWallBlock extends Block {
    public static final IntProperty HEIGHT=IntProperty.of("height",1,16);
    public static final MapCodec<TemporaryIceWallBlock> CODEC=createCodec(TemporaryIceWallBlock::new);
    private static VoxelShape[] shapes(){var result=new VoxelShape[17];for(int i=1;i<=16;i++)result[i]=Block.createCuboidShape(0,0,0,16,i,16);return result;}
    private static final VoxelShape[] SHAPES=shapes();
    public static final TemporaryIceWallBlock BLOCK=new TemporaryIceWallBlock(AbstractBlock.Settings.create().strength(-1,3600000).nonOpaque().dropsNothing());
    public TemporaryIceWallBlock(AbstractBlock.Settings settings){super(settings);setDefaultState(getStateManager().getDefaultState().with(HEIGHT,16));}
    public static void register(){net.minecraft.registry.Registry.register(net.minecraft.registry.Registries.BLOCK,net.minecraft.util.Identifier.of("owmcguest","temporary_ice_wall"),BLOCK);}
    @Override public MapCodec<TemporaryIceWallBlock> getCodec(){return CODEC;}
    @Override protected void appendProperties(StateManager.Builder<Block,BlockState> b){b.add(HEIGHT);}
    @Override public BlockRenderType getRenderType(BlockState state){return BlockRenderType.INVISIBLE;}
    @Override public VoxelShape getCollisionShape(BlockState state,BlockView w,BlockPos p,ShapeContext c){return SHAPES[state.get(HEIGHT)];}
    @Override public VoxelShape getOutlineShape(BlockState state,BlockView w,BlockPos p,ShapeContext c){return getCollisionShape(state,w,p,c);}
}
